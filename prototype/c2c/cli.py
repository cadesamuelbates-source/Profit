"""Command line: build a deal packet, mark it verified, and report metrics."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

from . import funnel, metrics
from .engine import DealError, Schedule, compute_schedule, fmt_time, load_json, schedule_to_json
from .ics import build_ics
from .outbox import build_outbox, reminder_dict
from .timeline_html import build_timeline_html

HERE = Path(__file__).resolve().parent.parent
DEFAULT_PROFILES = HERE / "profiles"
DEFAULT_METRICS = HERE / "data" / "metrics.jsonl"


def _now(value: str | None, tz) -> dt.datetime:
    if not value:
        return dt.datetime.now(tz)
    parsed = dt.datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=tz)


def build_checklist(schedule: Schedule) -> str:
    deal = schedule.deal
    lines = [
        f"# Verification checklist: deal {deal.get('deal_id')}",
        "",
        f"Profile: `{schedule.profile.get('profile_id')}`. Status: **{schedule.profile.get('status')}**",
        "",
        "Before anything is shared with a client, check every date below against the **fully executed**",
        "contract and all addenda. The effective date is the date of final acceptance (the last",
        "counteroffer signature), not the date the offer was drafted.",
        "",
    ]
    for d in schedule.deadlines:
        lines.append(
            f"- [ ] **{d.label}**: {d.due:%a %b} {d.due.day}, {d.due.year} {fmt_time(d.due)} {d.due:%Z}  "
        )
        lines.append(f"  computed: {d.explanation}  ")
        lines.append("  contract paragraph: ______  matches? Y / N")
    if schedule.warnings:
        lines += ["", "## Warnings (resolve or explain before sending)", ""]
        lines += [f"- {w}" for w in schedule.warnings]
    if schedule.skipped:
        lines += ["", "## Not in this contract (confirm they really are absent)", ""]
        lines += [f"- {s}" for s in schedule.skipped]
    lines += [
        "",
        "## Sign-off",
        "",
        "When every box is checked, run `python -m c2c verify <this folder>`. That records setup time.",
        "",
    ]
    return "\n".join(lines)


def cmd_build(args) -> int:
    try:
        deal = load_json(args.deal)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read deal sheet: {exc}", file=sys.stderr)
        return 2
    profile_name = str(deal.get("profile", ""))
    if not re.fullmatch(r"[A-Za-z0-9_-]+", profile_name):
        print(f"error: invalid profile name '{profile_name}'", file=sys.stderr)
        return 2
    profile_path = Path(args.profiles) / f"{profile_name}.json"
    if not profile_path.exists():
        print(f"error: profile '{profile_name}' not found in {args.profiles}", file=sys.stderr)
        return 2
    try:
        schedule = compute_schedule(deal, load_json(profile_path))
    except DealError as exc:
        print("error: deal sheet has problems:", file=sys.stderr)
        for err in exc.errors:
            print(f"  - {err}", file=sys.stderr)
        return 2

    now = _now(args.now, schedule.tz)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    reminders, dropped = build_outbox(schedule, now)

    (out / "schedule.json").write_text(json.dumps(schedule_to_json(schedule), indent=2))
    with open(out / "calendar.ics", "w", encoding="utf-8", newline="") as fh:
        fh.write(build_ics(schedule, now))
    (out / "timeline.html").write_text(build_timeline_html(schedule, now), encoding="utf-8")
    with open(out / "outbox.jsonl", "w", encoding="utf-8") as fh:
        for r in reminders:
            fh.write(json.dumps(reminder_dict(r)) + "\n")
    (out / "CHECKLIST.md").write_text(build_checklist(schedule), encoding="utf-8")

    log = Path(args.metrics)
    salt = metrics.get_salt(log)
    deal_ref = metrics.ref(str(deal.get("deal_id", "")), salt)
    agent_ref = metrics.ref(deal["agent"].get("email") or deal["agent"]["name"], salt)
    (out / ".refs.json").write_text(json.dumps({"deal_ref": deal_ref, "agent_ref": agent_ref}))
    metrics.log_event(
        log, "deal_built", now,
        deal_ref=deal_ref, agent_ref=agent_ref,
        deadlines=len(schedule.deadlines), reminders=len(reminders),
        dropped_past_reminders=dropped, warnings=len(schedule.warnings),
    )
    print(f"built {len(schedule.deadlines)} deadlines, {len(reminders)} reminders "
          f"({dropped} past reminders dropped), {len(schedule.warnings)} warnings -> {out}")
    print("NOT SENT: outbox is a dry run. Verify CHECKLIST.md before sharing anything.")
    return 0


def cmd_verify(args) -> int:
    refs_path = Path(args.packet) / ".refs.json"
    if not refs_path.exists():
        print(f"error: {args.packet} is not a built deal packet", file=sys.stderr)
        return 2
    refs = json.loads(refs_path.read_text())
    log = Path(args.metrics)
    first = metrics.first_built(log, refs["deal_ref"])
    now = _now(args.now, dt.timezone.utc)
    minutes = None
    if first:
        minutes = round((now - dt.datetime.fromisoformat(first["ts"])).total_seconds() / 60, 1)
    metrics.log_event(log, "deal_verified", now, setup_minutes=minutes, **refs)
    print(f"verified; setup time {minutes} min" if minutes is not None else "verified; no build event found")
    return 0


def cmd_summary(args) -> int:
    print(json.dumps(metrics.summarize(Path(args.metrics)), indent=2))
    return 0


def cmd_funnel(args) -> int:
    setup = metrics.summarize(Path(args.metrics))["median_setup_minutes"]
    as_of = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
    try:
        result = funnel.report(Path(args.tracker), Path(args.thresholds), setup, as_of)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="c2c", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="build a deal packet from a deal sheet")
    b.add_argument("deal")
    b.add_argument("--out", required=True)
    b.add_argument("--now", help="ISO datetime; defaults to the current time")
    b.add_argument("--profiles", default=str(DEFAULT_PROFILES))
    b.add_argument("--metrics", default=str(DEFAULT_METRICS))
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("verify", help="record that a packet was checked against the contract")
    v.add_argument("packet")
    v.add_argument("--now", help="ISO datetime (UTC if no offset); defaults to the current time")
    v.add_argument("--metrics", default=str(DEFAULT_METRICS))
    v.set_defaults(func=cmd_verify)

    s = sub.add_parser("summary", help="print usage metrics")
    s.add_argument("--metrics", default=str(DEFAULT_METRICS))
    s.set_defaults(func=cmd_summary)

    f = sub.add_parser("funnel", help="evaluate the validation tracker against pre-registered thresholds")
    f.add_argument("tracker")
    f.add_argument("--thresholds", required=True)
    f.add_argument("--metrics", default=str(DEFAULT_METRICS))
    f.add_argument("--as-of", help="YYYY-MM-DD; defaults to today")
    f.set_defaults(func=cmd_funnel)

    args = parser.parse_args(argv)
    return args.func(args)
