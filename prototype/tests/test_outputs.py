"""AC3 (calendar), AC4 (client page), AC5 (outbox)."""

import ast
import datetime as dt
import html
import re
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

from c2c.engine import compute_schedule
from c2c.ics import build_ics, escape_text, fold, uid_for
from c2c.outbox import QUIET_END, QUIET_START, build_outbox, clamp_send_time
from c2c.timeline_html import build_timeline_html

from helpers import ROOT, example_profile, sample_deal

CHI = ZoneInfo("America/Chicago")
NOW = dt.datetime(2026, 10, 17, 9, 0, tzinfo=CHI)


def schedule(deal=None):
    return compute_schedule(deal or sample_deal(), example_profile())


class CalendarFile(unittest.TestCase):
    def setUp(self):
        self.ics = build_ics(schedule(), NOW)

    def test_crlf_and_folding(self):
        self.assertTrue(self.ics.endswith("\r\n"))
        self.assertNotIn("\n", self.ics.replace("\r\n", ""))
        for line in self.ics.split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 75, line)

    def test_fold_never_splits_multibyte_characters(self):
        folded = fold("SUMMARY:" + "é" * 80)
        for line in folded.split("\r\n"):
            line.encode("utf-8").decode("utf-8")
            self.assertLessEqual(len(line.encode("utf-8")), 75)

    def test_escaping(self):
        self.assertEqual(escape_text("a,b;c\\d\ne"), "a\\,b\\;c\\\\d\\ne")

    def test_required_properties_and_alarm(self):
        events = self.ics.count("BEGIN:VEVENT")
        self.assertEqual(events, len(schedule().deadlines))
        for prop in ("UID:", "DTSTAMP:", "DTSTART:", "DTEND:"):
            self.assertEqual(self.ics.count("\r\n" + prop), events, prop)
        self.assertGreaterEqual(self.ics.count("BEGIN:VALARM"), events)

    def test_uid_is_stable(self):
        self.assertEqual(uid_for("DEMO", "closing"), uid_for("DEMO", "closing"))
        self.assertNotEqual(uid_for("DEMO", "closing"), uid_for("DEMO", "financing"))
        self.assertEqual(build_ics(schedule(), NOW), build_ics(schedule(), NOW))

    def test_dtend_is_due_time_in_utc(self):
        # Earnest money: Mon 2026-10-19 17:00 CDT == 22:00 UTC.
        self.assertIn("DTEND:20261019T220000Z", self.ics)
        # Closing: Fri 2026-11-20 10:00 CST (after DST ends) == 16:00 UTC.
        self.assertIn("DTEND:20261120T160000Z", self.ics)

    def test_independent_parser(self):
        try:
            import icalendar
        except ImportError:
            self.skipTest("icalendar package not installed")
        cal = icalendar.Calendar.from_ical(self.ics)
        events = [c for c in cal.walk() if c.name == "VEVENT"]
        self.assertEqual(len(events), len(schedule().deadlines))
        due = {str(e["SUMMARY"]): e.decoded("DTEND") for e in events}
        closing = next(v for k, v in due.items() if k.endswith("Closing"))
        self.assertEqual(closing, dt.datetime(2026, 11, 20, 16, 0, tzinfo=dt.timezone.utc))


class ClientPage(unittest.TestCase):
    def test_user_text_is_escaped(self):
        deal = sample_deal()
        deal["property_address"] = "<script>alert(1)</script>"
        deal["agent"]["name"] = "Eve \"<img src=x onerror=alert(2)>\""
        deal["parties"][3]["email"] = "x@example.com\"><script>alert(3)</script>"
        page = build_timeline_html(schedule(deal), NOW)
        self.assertNotIn("<script", page)
        self.assertNotIn("<img", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_no_external_resources(self):
        page = build_timeline_html(schedule(), NOW)
        for url in re.findall(r'(?:src|href)="([^"]*)"', page):
            self.assertRegex(url, r"^(tel:|mailto:)", url)
        self.assertNotIn("<script", page)
        self.assertNotIn("@import", page)

    def test_chronological_and_marks_client_actions(self):
        page = build_timeline_html(schedule(), NOW)
        labels = [d.label for d in schedule().deadlines]
        positions = [page.index(f'<div class="title">{html.escape(label)}') for label in labels]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Your action", page)

    def test_required_safety_text(self):
        page = build_timeline_html(schedule(), NOW)
        self.assertIn("Wire fraud warning", page)
        self.assertIn("The signed contract and its addenda govern", page)

    def test_other_side_principal_not_listed(self):
        page = build_timeline_html(schedule(), NOW)
        self.assertNotIn("Pat Lee", page)
        self.assertNotIn("pat.lee@example.net", page)
        self.assertIn("Morgan Blake", page)  # listing agent is the right contact

    def test_next_up_is_first_future_deadline(self):
        page = build_timeline_html(schedule(), NOW)
        self.assertIn("Next: Earnest money delivered to escrow", page)
        later = build_timeline_html(schedule(), dt.datetime(2026, 10, 25, 9, 0, tzinfo=CHI))
        self.assertIn("Next: Seller response to repair request expected", later)
        self.assertIn("date passed", later)


class Outbox(unittest.TestCase):
    def setUp(self):
        self.reminders, self.dropped = build_outbox(schedule(), NOW)

    def test_no_reminder_in_the_past_and_drops_are_counted(self):
        for r in self.reminders:
            self.assertGreaterEqual(dt.datetime.fromisoformat(r.send_at), NOW)
        # Earnest money (due Mon 10-19): the 2-days-before slot (Sat 10-17 09:00) equals NOW,
        # so it is kept; nothing earlier exists in the sample.
        late, dropped = build_outbox(schedule(), dt.datetime(2026, 10, 20, 9, 0, tzinfo=CHI))
        self.assertGreater(dropped, 0)

    def test_quiet_hours_and_before_due(self):
        dues = {d.key: d.due for d in schedule().deadlines}
        for r in self.reminders:
            at = dt.datetime.fromisoformat(r.send_at)
            self.assertTrue(QUIET_START <= at.time() <= QUIET_END, r.send_at)
            if r.deadline_key != "digest":
                for key in r.deadline_key.split("+"):
                    self.assertLess(at, dues[key])

    def test_sms_only_with_consent(self):
        deal = sample_deal()
        no_consent = {p["phone"] for p in deal["parties"] if p.get("phone") and p.get("sms_consent") is not True}
        sms_to = {r.address for r in self.reminders if r.channel == "sms"}
        self.assertFalse(no_consent & sms_to)
        self.assertIn("(555) 010-3000", sms_to)  # buyer who consented
        for r in self.reminders:
            if r.channel == "sms":
                self.assertIn("Reply STOP to opt out", r.body)

    def test_one_message_per_person_per_day(self):
        keys = [(r.recipient_name, r.send_at[:10]) for r in self.reminders]
        self.assertEqual(len(keys), len(set(keys)))

    def test_routing_owner_and_other_side(self):
        by_deadline = {}
        for r in self.reminders:
            for key in r.deadline_key.split("+"):
                by_deadline.setdefault(key, set()).add(r.recipient_role)
        self.assertEqual(by_deadline["earnest_money"], {"buyer"})
        self.assertEqual(by_deadline["appraisal"], {"lender"})
        # Seller-owned deadline on a buyer-side file goes to the listing agent, never the seller.
        self.assertEqual(by_deadline["inspection_response"], {"listing_agent"})
        self.assertNotIn("seller", {r.recipient_role for r in self.reminders})
        self.assertNotIn("pat.lee@example.net", {r.address for r in self.reminders})

    def test_agent_gets_at_most_one_digest_per_day_and_nothing_else(self):
        agent = [r for r in self.reminders if r.recipient_role == "agent"]
        self.assertTrue(agent)
        self.assertTrue(all(r.deadline_key == "digest" and r.channel == "email" for r in agent))
        days = [r.send_at[:10] for r in agent]
        self.assertEqual(len(days), len(set(days)))

    def test_volume_is_reasonable_for_one_file(self):
        # The first demo run queued 78 messages; the routing rules must keep it far lower.
        self.assertLessEqual(len(self.reminders), 40)

    def test_clamp_rules(self):
        due = dt.datetime(2026, 11, 2, 8, 30, tzinfo=CHI)
        same_day = clamp_send_time(dt.datetime(2026, 11, 2, 9, 0, tzinfo=CHI), due)
        self.assertEqual(same_day, dt.datetime(2026, 11, 1, 19, 0, tzinfo=CHI))
        late = clamp_send_time(dt.datetime(2026, 11, 1, 22, 0, tzinfo=CHI), due)
        self.assertEqual(late, dt.datetime(2026, 11, 1, 20, 0, tzinfo=CHI))

    def test_outbox_module_has_no_network_imports(self):
        tree = ast.parse((ROOT / "c2c" / "outbox.py").read_text())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertFalse(imported & {"socket", "smtplib", "urllib", "http", "requests", "ssl"})


if __name__ == "__main__":
    unittest.main()
