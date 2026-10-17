"""Reminder outbox. Dry run only: this module builds messages and never sends them.

Sending needs a provider account, A2P 10DLC registration for SMS, and recorded
consent. None of that is in scope until the founder approves it.

Routing rules:
- The owner of each deadline gets reminders at the profile's lead times, on one
  channel: SMS with consent, otherwise email.
- Deadlines owned by the *other side's* principal go to that side's agent, never
  to the principal directly.
- The agent gets one 08:00 email digest two days before each deadline, listing
  everything due in the next two days. Overlapping digests merge into one per day.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass

from .engine import ROLE_LABELS, Schedule, fmt_time

QUIET_START = dt.time(8, 0)
QUIET_END = dt.time(20, 0)
DIGEST_AT = dt.time(8, 0)
DIGEST_HORIZON_DAYS = 2
DEFAULT_LEADS = [{"days_before": 2, "at": "09:00"}, {"days_before": 0, "at": "09:00"}]
OTHER_SIDE_AGENT = {"buyer": "listing_agent", "seller": "buyer_agent"}


@dataclass(frozen=True)
class Reminder:
    deadline_key: str  # "digest" for the agent's daily digest
    recipient_role: str
    recipient_name: str
    channel: str  # "sms" | "email"
    address: str
    send_at: str  # ISO 8601, deal-local
    subject: str
    body: str


def clamp_send_time(candidate: dt.datetime, due: dt.datetime) -> dt.datetime | None:
    """Move a send time inside quiet hours and strictly before the deadline.

    A send time at or after the deadline moves to one hour before it; anything
    earlier than 08:00 moves to 19:00 the previous evening. Returns None if no
    acceptable time remains.
    """
    if candidate >= due:
        candidate = due - dt.timedelta(hours=1)
    if candidate.time() < QUIET_START:
        prev = candidate.date() - dt.timedelta(days=1)
        candidate = dt.datetime.combine(prev, dt.time(19, 0), tzinfo=candidate.tzinfo)
    elif candidate.time() > QUIET_END:
        candidate = dt.datetime.combine(candidate.date(), QUIET_END, tzinfo=candidate.tzinfo)
    if candidate >= due:
        return None
    return candidate


def recipients_for(schedule: Schedule, owner: str) -> list[tuple[str, dict]]:
    deal = schedule.deal
    client = deal["client_role"]
    if owner == "agent":
        return []  # covered by the digest
    if owner in OTHER_SIDE_AGENT and owner != client:
        owner = OTHER_SIDE_AGENT[client]
    return [(p["role"], p) for p in deal.get("parties", []) if p["role"] == owner]


def _channel(person: dict) -> tuple[str, str] | None:
    if person.get("phone") and person.get("sms_consent") is True:
        return "sms", person["phone"]
    if person.get("email"):
        return "email", person["email"]
    return None


def _when(due: dt.datetime) -> str:
    return f"{due:%a %b} {due.day}, {fmt_time(due)} {due:%Z}"


def build_outbox(schedule: Schedule, now: dt.datetime) -> tuple[list[Reminder], int]:
    """Return (reminders, dropped_past_count)."""
    deal = schedule.deal
    leads = schedule.profile.get("reminders", DEFAULT_LEADS)
    agent = deal["agent"]
    agent_first = (agent.get("name") or "your agent").split()[0]
    client = deal["client_role"]
    out: list[tuple[dt.datetime, Reminder]] = []
    dropped = 0

    # Bundle per recipient per day: (role, name, channel, address, date) -> [(send_at, deadline)]
    bundles: dict[tuple, list[tuple[dt.datetime, object]]] = {}
    for d in schedule.deadlines:
        people = recipients_for(schedule, d.owner)
        for lead in leads:
            day = d.due.date() - dt.timedelta(days=int(lead["days_before"]))
            at = dt.time.fromisoformat(lead["at"])
            send_at = clamp_send_time(dt.datetime.combine(day, at, tzinfo=d.due.tzinfo), d.due)
            if send_at is None:
                continue
            if send_at < now:
                dropped += 1
                continue
            for role, person in people:
                route = _channel(person)
                if route is None:
                    continue
                key = (role, person.get("name", ""), *route, send_at.date())
                bundles.setdefault(key, []).append((send_at, d))

    for (role, name, channel, addr, _day), items in bundles.items():
        # The earliest slot precedes every bundled deadline, since each slot precedes its own.
        send_at = min(s for s, _ in items)
        deadlines = sorted({d for _, d in items}, key=lambda d: d.due)
        texts = []
        for d in deadlines:
            text = f"{d.label} is due {_when(d.due)}."
            if role == client and d.action:
                text += f" {d.action}"
            texts.append(text)
        if channel == "sms":
            body = f"Reminder from {agent_first}'s team: {' '.join(texts)} Reply STOP to opt out."
        else:
            body = ("\n".join(texts) + f"\n\nProperty: {deal.get('property_address', '')}\n\n"
                    "The signed contract governs; reply to this email with any questions.")
        subject = (f"Reminder: {deadlines[0].label} due {_when(deadlines[0].due)}" if len(deadlines) == 1
                   else f"Reminder: {len(deadlines)} deadlines coming up")
        out.append((send_at, Reminder("+".join(d.key for d in deadlines), role, name, channel, addr,
                                      send_at.isoformat(), subject, body)))

    if agent.get("email"):
        # Lead time is what lets an agent prevent a miss; same-day nudges go to the owner.
        digest_days = sorted({d.due.date() - dt.timedelta(days=DIGEST_HORIZON_DAYS) for d in schedule.deadlines})
        for day in digest_days:
            send_at = dt.datetime.combine(day, DIGEST_AT, tzinfo=schedule.tz)
            items = [d for d in schedule.deadlines
                     if day <= d.due.date() <= day + dt.timedelta(days=DIGEST_HORIZON_DAYS) and d.due > send_at]
            if not items:
                continue
            if send_at < now:
                dropped += 1
                continue
            lines = [f"- {_when(d.due)}: {d.label} (responsible: {ROLE_LABELS.get(d.owner, d.owner)})" for d in items]
            body = (f"Deadlines in the next {DIGEST_HORIZON_DAYS} days for {deal.get('property_address', '')}:\n"
                    + "\n".join(lines))
            out.append((send_at, Reminder("digest", "agent", agent.get("name", ""), "email", agent["email"],
                                          send_at.isoformat(), f"{len(items)} deadline(s) coming up", body)))

    out.sort(key=lambda pair: pair[0])
    return [r for _, r in out], dropped


def reminder_dict(reminder: Reminder) -> dict:
    return asdict(reminder)
