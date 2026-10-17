"""RFC 5545 calendar output. Times are written in UTC so no VTIMEZONE is needed."""

from __future__ import annotations

import datetime as dt
import hashlib

from .engine import Schedule, fmt_time

PRODID = "-//Contract-to-Close Desk//c2c 0.1//EN"


def escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def fold(line: str) -> str:
    """Fold a content line to <= 75 octets without splitting a UTF-8 character."""
    out, current, size = [], "", 0
    limit = 75
    for ch in line:
        width = len(ch.encode("utf-8"))
        if size + width > limit:
            out.append(current)
            current, size = " ", 1  # continuation lines start with one space
        current += ch
        size += width
    out.append(current)
    return "\r\n".join(out)


def _utc(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def uid_for(deal_id: str, key: str) -> str:
    digest = hashlib.sha256(f"{deal_id}|{key}".encode()).hexdigest()[:20]
    return f"{digest}@c2c.invalid"


def build_ics(schedule: Schedule, now: dt.datetime) -> str:
    deal = schedule.deal
    address = deal.get("property_address", "")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for d in schedule.deadlines:
        start = d.due - dt.timedelta(minutes=30)
        description = f"{d.meaning}\n\nAction: {d.action}\n\nHow this date was computed: {d.explanation}"
        description += "\n\nThe signed contract governs. Confirm with your agent."
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid_for(str(deal.get('deal_id', '')), d.key)}",
            f"DTSTAMP:{_utc(now)}",
            f"DTSTART:{_utc(start)}",
            f"DTEND:{_utc(d.due)}",
            f"SUMMARY:{escape_text(f'DEADLINE {fmt_time(d.due)}: {d.label}')}",
            f"LOCATION:{escape_text(address)}",
            f"DESCRIPTION:{escape_text(description)}",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "TRIGGER:-P1D",
            f"DESCRIPTION:{escape_text('Tomorrow: ' + d.label)}",
            "END:VALARM",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "TRIGGER:-PT2H",
            f"DESCRIPTION:{escape_text('In 2 hours: ' + d.label)}",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"
