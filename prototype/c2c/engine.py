"""Deal-sheet validation and deadline computation."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .holidays_us import is_federal_holiday

ROLES = {"buyer", "seller", "lender", "title", "buyer_agent", "listing_agent", "agent"}
COUNTS = {"calendar", "business"}
ROLLS = {"none", "forward", "backward"}


class DealError(ValueError):
    """Raised when a deal sheet or profile can't produce a trustworthy schedule."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class Deadline:
    key: str
    label: str
    due: dt.datetime  # timezone-aware, local to the deal
    owner: str
    meaning: str
    action: str
    explanation: str
    warnings: tuple[str, ...] = ()

    @property
    def date(self) -> dt.date:
        return self.due.date()


@dataclass
class Schedule:
    deal: dict
    profile: dict
    tz: ZoneInfo
    deadlines: list[Deadline]
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BusinessCalendar:
    def __init__(self, extra_holidays: list[str] | None = None, federal: bool = True):
        self.federal = federal
        self.extra = {dt.date.fromisoformat(d) for d in (extra_holidays or [])}

    def is_business_day(self, day: dt.date) -> bool:
        if day.weekday() >= 5 or day in self.extra:
            return False
        return not (self.federal and is_federal_holiday(day))

    def add_business_days(self, start: dt.date, n: int) -> dt.date:
        step = 1 if n >= 0 else -1
        day, remaining = start, abs(n)
        while remaining:
            day += dt.timedelta(days=step)
            if self.is_business_day(day):
                remaining -= 1
        return day

    def roll(self, day: dt.date, mode: str) -> dt.date:
        if mode == "none":
            return day
        step = 1 if mode == "forward" else -1
        while not self.is_business_day(day):
            day += dt.timedelta(days=step)
        return day


def load_json(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _parse_date(value, name: str, errors: list[str]) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value))
    except (TypeError, ValueError):
        errors.append(f"{name}: '{value}' is not a valid YYYY-MM-DD date")
        return None


def _fmt(day: dt.date) -> str:
    return f"{day:%a %b} {day.day}, {day.year}"


def fmt_time(moment: dt.datetime) -> str:
    """'5:00 PM' without platform-specific strftime flags."""
    return f"{moment.hour % 12 or 12}:{moment:%M %p}"


ROLE_LABELS = {
    "buyer": "Buyer",
    "seller": "Seller",
    "lender": "Lender",
    "title": "Title / escrow",
    "buyer_agent": "Buyer's agent",
    "listing_agent": "Listing agent",
    "agent": "Your agent",
}


def _validate_profile(profile: dict) -> list[str]:
    errors = []
    keys = set()
    for i, rule in enumerate(profile.get("deadlines", [])):
        where = f"profile deadline #{i + 1} ({rule.get('key', '?')})"
        for req in ("key", "label", "anchor", "owner"):
            if req not in rule:
                errors.append(f"{where}: missing '{req}'")
        if rule.get("count", "calendar") not in COUNTS:
            errors.append(f"{where}: count must be one of {sorted(COUNTS)}")
        if rule.get("roll", "none") not in ROLLS:
            errors.append(f"{where}: roll must be one of {sorted(ROLLS)}")
        if rule.get("direction", "after") not in ("after", "before"):
            errors.append(f"{where}: direction must be 'after' or 'before'")
        fixed = rule.get("days", {}).get("fixed", 0)
        if isinstance(fixed, bool) or not isinstance(fixed, int) or fixed < 0:
            errors.append(f"{where}: days.fixed must be a whole number >= 0")
        if rule.get("owner") not in ROLES:
            errors.append(f"{where}: owner must be one of {sorted(ROLES)}")
        try:
            dt.time.fromisoformat(rule.get("due_time", "17:00"))
        except (TypeError, ValueError):
            errors.append(f"{where}: due_time must be HH:MM")
        anchor = rule.get("anchor")
        if anchor not in ("effective_date", "closing_date") and anchor not in keys:
            errors.append(
                f"{where}: anchor '{anchor}' is not effective_date, closing_date, "
                "or an earlier deadline key"
            )
        keys.add(rule.get("key"))
    if not profile.get("deadlines"):
        errors.append("profile has no deadlines")
    return errors


def _validate_parties(deal: dict, errors: list[str]) -> None:
    agent = deal.get("agent")
    if not isinstance(agent, dict) or not agent.get("name"):
        errors.append("agent: name is required")
    for i, party in enumerate(deal.get("parties", [])):
        if party.get("role") not in ROLES:
            errors.append(f"parties[{i}]: role must be one of {sorted(ROLES)}")
        if not party.get("name"):
            errors.append(f"parties[{i}]: name is required")


def compute_schedule(deal: dict, profile: dict) -> Schedule:
    """Validate the deal against the profile and compute every deadline.

    Raises DealError listing every problem found, so the operator can fix them
    all in one pass.
    """
    errors = _validate_profile(profile)
    tz_name = deal.get("timezone") or profile.get("timezone")
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, TypeError, ValueError):
        errors.append(f"timezone: '{tz_name}' is not a known IANA timezone")
        tz = None

    effective = _parse_date(deal.get("effective_date"), "effective_date", errors)
    closing = _parse_date(deal.get("closing_date"), "closing_date", errors)
    if effective and closing and closing < effective:
        errors.append(
            f"closing_date {closing} is before effective_date {effective}"
        )
    if deal.get("client_role") not in ("buyer", "seller"):
        errors.append("client_role must be 'buyer' or 'seller'")
    _validate_parties(deal, errors)

    terms = deal.get("terms") or {}
    for name, value in terms.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"terms.{name}: must be a whole number of days >= 0, got {value!r}")

    if errors:
        raise DealError(errors)

    cal = BusinessCalendar(profile.get("extra_holidays"), profile.get("federal_holidays", True))
    anchors = {"effective_date": effective, "closing_date": closing}
    anchor_names = {"effective_date": "effective date", "closing_date": "closing date"}
    deadlines: list[Deadline] = []
    skipped: list[str] = []
    warnings: list[str] = []

    for rule in profile["deadlines"]:
        days_spec = rule.get("days", {"fixed": 0})
        if "term" in days_spec:
            n = terms.get(days_spec["term"])
            if n is None:
                if rule.get("optional"):
                    skipped.append(f"{rule['label']} (no '{days_spec['term']}' in this contract)")
                    continue
                errors.append(f"terms.{days_spec['term']}: required for '{rule['label']}'")
                continue
        else:
            n = int(days_spec.get("fixed", 0))
        anchor_key = rule["anchor"]
        if anchor_key not in anchors:
            # Anchor was an optional deadline that this contract doesn't have.
            skipped.append(f"{rule['label']} (depends on skipped '{anchor_key}')")
            continue
        base = anchors[anchor_key]
        sign = -1 if rule.get("direction", "after") == "before" else 1
        count = rule.get("count", "calendar")
        if count == "business":
            raw = cal.add_business_days(base, sign * n)
        else:
            raw = base + dt.timedelta(days=sign * n)
        roll = rule.get("roll", "none")
        final = cal.roll(raw, roll)

        unit = "business day" if count == "business" else "calendar day"
        rel = "before" if sign < 0 else "after"
        if n == 0:
            explanation = f"{anchor_names.get(anchor_key, anchor_key)} as written: {_fmt(base)}"
        else:
            explanation = (
                f"{anchor_names.get(anchor_key, anchor_key)} {_fmt(base)} "
                f"{'-' if sign < 0 else '+'} {n} {unit}{'s' if n != 1 else ''} ({rel}) = {_fmt(raw)}"
            )
        dl_warnings = []
        if final != raw:
            explanation += f"; not a business day, rolled {roll} to {_fmt(final)}"
        elif roll == "none" and not cal.is_business_day(raw) and not (anchor_key == "closing_date" and n == 0):
            explanation += "; falls on a non-business day and this rule does NOT roll"
            dl_warnings.append(
                f"'{rule['label']}' lands on {_fmt(final)} (non-business day) and does not roll; "
                "confirm the contract's weekend/holiday rule for this deadline"
            )

        due_time = dt.time.fromisoformat(rule.get("due_time", "17:00"))
        due = dt.datetime.combine(final, due_time, tzinfo=tz)
        if rule["key"] != "closing" and final > closing:
            dl_warnings.append(f"'{rule['label']}' ({_fmt(final)}) falls after closing ({_fmt(closing)})")
        warnings.extend(dl_warnings)
        deadlines.append(
            Deadline(
                key=rule["key"],
                label=rule["label"],
                due=due,
                owner=rule["owner"],
                meaning=rule.get("meaning", ""),
                action=rule.get("action", ""),
                explanation=explanation,
                warnings=tuple(dl_warnings),
            )
        )
        anchors[rule["key"]] = final
        anchor_names[rule["key"]] = rule["label"]

    if errors:
        raise DealError(errors)
    if not cal.is_business_day(closing):
        warnings.append(f"closing date {_fmt(closing)} is not a business day")
    deadlines.sort(key=lambda d: d.due)
    return Schedule(deal=deal, profile=profile, tz=tz, deadlines=deadlines, skipped=skipped, warnings=warnings)


def schedule_to_json(schedule: Schedule) -> dict:
    return {
        "deal_id": schedule.deal.get("deal_id"),
        "profile": schedule.profile.get("profile_id"),
        "profile_status": schedule.profile.get("status"),
        "timezone": str(schedule.tz),
        "deadlines": [
            {
                "key": d.key,
                "label": d.label,
                "due": d.due.isoformat(),
                "owner": d.owner,
                "explanation": d.explanation,
                "warnings": list(d.warnings),
            }
            for d in schedule.deadlines
        ],
        "skipped": schedule.skipped,
        "warnings": schedule.warnings,
    }
