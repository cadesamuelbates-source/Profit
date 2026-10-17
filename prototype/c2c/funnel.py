"""Validation funnel: count each evidence stage separately and apply the
pre-registered decision rule in validation/thresholds.json.

Stages are deliberately distinct. A compliment is not a click, a signup is not
a commitment, and a commitment is not a payment. Only cleared, unrefunded
payments count as paid.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

YES = {"y", "yes", "true", "1"}


def _yes(value: str | None) -> bool:
    return (value or "").strip().lower() in YES


def _date(value: str | None) -> dt.date | None:
    value = (value or "").strip()
    return dt.date.fromisoformat(value) if value else None


def thresholds_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


DATE_FIELDS = ("contacted_on", "first_paid_on", "second_paid_on")


def load_rows(tracker: Path) -> list[dict]:
    with open(tracker, newline="", encoding="utf-8") as fh:
        rows = [row for row in csv.DictReader(fh) if (row.get("contact_id") or "").strip()]
    bad = []
    for row in rows:
        for name in DATE_FIELDS:
            try:
                _date(row.get(name))
            except ValueError:
                bad.append(f"{row['contact_id']}.{name}={row.get(name)!r}")
    if bad:
        raise ValueError("tracker has invalid YYYY-MM-DD dates: " + ", ".join(bad))
    return rows


def count_stages(rows: list[dict], repeat_window_days: int, paid_window_days: int) -> dict:
    qualified = [r for r in rows if _yes(r.get("qualified"))]
    contacted = [r for r in qualified if _date(r.get("contacted_on"))]

    def paid_in_window(r: dict) -> bool:
        contacted_on, paid_on = _date(r.get("contacted_on")), _date(r.get("first_paid_on"))
        refunded = _yes(r.get("refunded"))
        return bool(contacted_on and paid_on and not refunded
                    and (paid_on - contacted_on).days <= paid_window_days)

    paid = [r for r in contacted if paid_in_window(r)]

    def repeat(r: dict) -> bool:
        first, second = _date(r.get("first_paid_on")), _date(r.get("second_paid_on"))
        return bool(first and second and (second - first).days <= repeat_window_days)

    interviewed = [r for r in contacted if _yes(r.get("interviewed"))]
    repeat_windows_close = [
        _date(r["first_paid_on"]) + dt.timedelta(days=repeat_window_days) for r in paid if not repeat(r)
    ]
    return {
        "qualified_contacted": len(contacted),
        "replied": sum(_yes(r.get("replied")) for r in contacted),
        "interviewed": len(interviewed),
        "pain_top3": sum(_yes(r.get("pain_top3")) for r in interviewed),
        "compliment_only": sum(_yes(r.get("compliment_only")) for r in contacted),
        "viewed_demo": sum(_yes(r.get("viewed_demo")) for r in contacted),
        "submitted_deal_sheet": sum(_yes(r.get("submitted_deal_sheet")) for r in contacted),
        "written_commitment": sum(_yes(r.get("written_commitment")) for r in contacted),
        "paid_agents": len(paid),
        "repeat_paid_agents": sum(repeat(r) for r in paid),
        "client_visible_date_errors": sum(int(r.get("client_visible_date_errors") or 0) for r in contacted),
        "revenue_usd": round(sum(float(r.get("revenue_usd") or 0) for r in paid), 2),
        "last_repeat_window_closes": max(repeat_windows_close).isoformat() if repeat_windows_close else None,
    }


def decide(counts: dict, setup_median: float | None, rules: dict, as_of: dt.date) -> tuple[str, list[str]]:
    """Apply the pre-registered rule. Returns (decision, reasons).

    Absolute-count continue checks may pass before all contacts are made (fewer
    contacts only makes the rate better); STOP can only be declared after the
    full sample, so a slow start can't end the test early.
    """
    c, s = rules["continue"], rules["stop"]
    if counts["client_visible_date_errors"] > s["max_client_visible_date_errors"]:
        return "STOP", ["a date error reached a client (the accuracy promise was broken)"]
    checks = {
        f"paid agents >= {c['min_paid_agents']}": counts["paid_agents"] >= c["min_paid_agents"],
        f"repeat paid agents >= {c['min_repeat_paid_agents']}": counts["repeat_paid_agents"] >= c["min_repeat_paid_agents"],
        f"median setup <= {c['max_median_setup_minutes']} min": setup_median is not None
        and setup_median <= c["max_median_setup_minutes"],
    }
    failed = [name for name, ok in checks.items() if not ok]
    if not failed:
        return "CONTINUE", [f"all continue checks met: {', '.join(checks)}"]
    if counts["qualified_contacted"] < rules["min_qualified_contacts"]:
        return "INSUFFICIENT DATA", [
            f"{counts['qualified_contacted']} of {rules['min_qualified_contacts']} qualified contacts made"
        ] + [f"not yet met: {name}" for name in failed]

    interviewed = counts["interviewed"]
    pain_share = counts["pain_top3"] / interviewed if interviewed else 0.0
    if counts["paid_agents"] == 0:
        return "STOP", ["no qualified agent paid within the window"]
    weak_pain = interviewed >= s["min_interviews_for_pain_test"] and pain_share < s["min_pain_share"]
    if counts["paid_agents"] < c["min_paid_agents"] and weak_pain:
        return "STOP", [
            f"only {counts['paid_agents']} paid and {pain_share:.0%} of interviewed agents rank this a top-3 problem"
        ]
    window = counts.get("last_repeat_window_closes")
    only_repeat_missing = failed == [f"repeat paid agents >= {c['min_repeat_paid_agents']}"]
    if only_repeat_missing and window and as_of <= dt.date.fromisoformat(window):
        return "PENDING", [f"repeat-purchase window open until {window}"]
    return "ITERATE", [f"not met: {name}" for name in failed]


def report(tracker: Path, thresholds: Path, setup_median: float | None, as_of: dt.date) -> dict:
    rules = json.loads(thresholds.read_text())
    counts = count_stages(load_rows(tracker), rules["repeat_window_days"], rules["paid_window_days"])
    decision, reasons = decide(counts, setup_median, rules, as_of)
    return {
        "thresholds_sha256": thresholds_digest(thresholds),
        "counts": counts,
        "median_setup_minutes": setup_median,
        "decision": decision,
        "reasons": reasons,
    }
