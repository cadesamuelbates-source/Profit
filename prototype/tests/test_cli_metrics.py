"""AC6 (no PII in metrics, setup time), AC7 (end-to-end CLI), and the funnel decision rule."""

import csv
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from c2c import funnel

from helpers import ROOT, SAMPLE_DEAL, sample_deal

THRESHOLDS = ROOT.parent / "validation" / "thresholds.json"


def run(*args, env_extra=None):
    env = {**os.environ, "PYTHONPATH": str(ROOT), "C2C_METRICS_SALT": "test-salt", **(env_extra or {})}
    return subprocess.run([sys.executable, "-m", "c2c", *args], capture_output=True, text=True, env=env, cwd=ROOT)


class EndToEnd(unittest.TestCase):
    def test_build_verify_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, log = Path(tmp) / "packet", Path(tmp) / "metrics.jsonl"
            start = time.perf_counter()
            res = run("build", str(SAMPLE_DEAL), "--out", str(out), "--now", "2026-10-17T09:00", "--metrics", str(log))
            elapsed = time.perf_counter() - start
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertLess(elapsed, 2.0)
            for name in ("schedule.json", "calendar.ics", "timeline.html", "outbox.jsonl", "CHECKLIST.md"):
                self.assertTrue((out / name).exists(), name)
            self.assertIn("NOT SENT", res.stdout)

            res = run("verify", str(out), "--now", "2026-10-17T14:25:00+00:00", "--metrics", str(log))
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("setup time 25.0 min", res.stdout)

            summary = json.loads(run("summary", "--metrics", str(log)).stdout)
            self.assertEqual(summary["deals_built"], 1)
            self.assertEqual(summary["deals_verified"], 1)
            self.assertEqual(summary["median_setup_minutes"], 25.0)

            # AC6: no personal data in the metrics log.
            text = log.read_text()
            deal = sample_deal()
            pii = [deal["property_address"], deal["agent"]["name"], deal["agent"]["email"], deal["agent"]["phone"]]
            for p in deal["parties"]:
                pii += [p.get("name"), p.get("email"), p.get("phone")]
            for value in filter(None, pii):
                self.assertNotIn(value, text)
                self.assertNotIn(value.lower(), text.lower())
            for line in text.splitlines():
                record = json.loads(line)
                self.assertTrue(set(record) <= {"event", "ts", "deal_ref", "agent_ref", "deadlines",
                                                "reminders", "dropped_past_reminders", "warnings",
                                                "setup_minutes"}, record.keys())

    def test_repeat_agent_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "m.jsonl"
            for i in range(2):
                deal = sample_deal()
                deal["deal_id"] = f"DEMO-{i}"
                path = Path(tmp) / f"d{i}.json"
                path.write_text(json.dumps(deal))
                self.assertEqual(run("build", str(path), "--out", str(Path(tmp) / f"p{i}"),
                                     "--now", "2026-10-17T09:00", "--metrics", str(log)).returncode, 0)
            summary = json.loads(run("summary", "--metrics", str(log)).stdout)
            self.assertEqual(summary["unique_agents"], 1)
            self.assertEqual(summary["repeat_agents"], 1)

    def test_bad_deal_exits_nonzero_with_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            deal = sample_deal()
            deal["closing_date"] = "2026-10-01"
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(deal))
            res = run("build", str(path), "--out", str(Path(tmp) / "x"), "--metrics", str(Path(tmp) / "m.jsonl"))
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("before effective_date", res.stderr)
            self.assertFalse((Path(tmp) / "x").exists())

    def test_profile_name_cannot_traverse_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            deal = sample_deal()
            deal["profile"] = "../../etc/passwd"
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(deal))
            res = run("build", str(path), "--out", str(Path(tmp) / "x"), "--metrics", str(Path(tmp) / "m.jsonl"))
            self.assertEqual(res.returncode, 2)
            self.assertIn("invalid profile name", res.stderr)


FIELDS = ["contact_id", "qualified", "contacted_on", "replied", "interviewed", "pain_top3",
          "compliment_only", "viewed_demo", "submitted_deal_sheet", "written_commitment",
          "first_paid_on", "second_paid_on", "refunded", "revenue_usd", "client_visible_date_errors"]


def tracker(rows):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="")
    writer = csv.DictWriter(tmp, fieldnames=FIELDS)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in FIELDS})
    tmp.close()
    return Path(tmp.name)


def contacts(n, **extra):
    return [{"contact_id": f"A{i}", "qualified": "y", "contacted_on": "2026-11-01", "interviewed": "y", **extra}
            for i in range(n)]


class FunnelDecision(unittest.TestCase):
    AS_OF = dt.date(2027, 3, 1)

    def decide(self, rows, setup=20.0, as_of=None):
        return funnel.report(tracker(rows), THRESHOLDS, setup, as_of or self.AS_OF)

    def test_insufficient_sample_cannot_stop(self):
        self.assertEqual(self.decide(contacts(10))["decision"], "INSUFFICIENT DATA")

    def test_zero_payers_after_full_sample_stops(self):
        self.assertEqual(self.decide(contacts(40, pain_top3="y"))["decision"], "STOP")

    def test_compliments_and_commitments_are_not_payments(self):
        rows = contacts(40, compliment_only="y", viewed_demo="y", written_commitment="y", pain_top3="y")
        result = self.decide(rows)
        self.assertEqual(result["counts"]["paid_agents"], 0)
        self.assertEqual(result["decision"], "STOP")

    def test_continue_requires_payment_repeat_and_setup(self):
        rows = contacts(40, pain_top3="y")
        for r in rows[:4]:
            r.update(first_paid_on="2026-11-10", revenue_usd="129")
        for r in rows[:2]:
            r.update(second_paid_on="2026-12-15")
        self.assertEqual(self.decide(rows)["decision"], "CONTINUE")
        self.assertEqual(self.decide(rows, setup=45.0)["decision"], "ITERATE")

    def test_refunds_and_late_payments_do_not_count(self):
        rows = contacts(40, pain_top3="y")
        rows[0].update(first_paid_on="2026-11-10", refunded="y")
        rows[1].update(first_paid_on="2027-01-20")  # > 30 days after contact
        result = self.decide(rows)
        self.assertEqual(result["counts"]["paid_agents"], 0)

    def test_repeat_window_open_is_pending(self):
        rows = contacts(40, pain_top3="y")
        for r in rows[:4]:
            r.update(first_paid_on="2026-11-10")
        self.assertEqual(self.decide(rows, as_of=dt.date(2026, 12, 1))["decision"], "PENDING")
        self.assertEqual(self.decide(rows, as_of=dt.date(2027, 2, 1))["decision"], "ITERATE")

    def test_client_visible_error_stops(self):
        rows = contacts(5)
        rows[0]["client_visible_date_errors"] = "1"
        self.assertEqual(self.decide(rows)["decision"], "STOP")

    def test_weak_pain_and_few_payers_stops(self):
        rows = contacts(40, pain_top3="n")
        rows[0].update(first_paid_on="2026-11-10")
        self.assertEqual(self.decide(rows)["decision"], "STOP")

    def test_report_carries_threshold_hash(self):
        result = self.decide(contacts(1))
        self.assertEqual(len(result["thresholds_sha256"]), 64)

    def test_bad_tracker_date_is_reported_by_row(self):
        rows = contacts(2)
        rows[1]["first_paid_on"] = "11/10/2026"
        res = run("funnel", str(tracker(rows)), "--thresholds", str(THRESHOLDS), "--as-of", "2027-01-01",
                  "--metrics", str(Path(tempfile.gettempdir()) / "c2c-none.jsonl"))
        self.assertEqual(res.returncode, 2)
        self.assertIn("A1.first_paid_on", res.stderr)


if __name__ == "__main__":
    unittest.main()
