"""Business-metric events without personal data.

Deal and agent identifiers are salted SHA-256 prefixes. Names, emails, phone
numbers and addresses are never written to the log.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import secrets
import statistics
from pathlib import Path


def get_salt(log_path: Path) -> str:
    env = os.environ.get("C2C_METRICS_SALT")
    if env:
        return env
    salt_file = log_path.with_suffix(".salt")
    if salt_file.exists():
        return salt_file.read_text().strip()
    salt_file.parent.mkdir(parents=True, exist_ok=True)
    salt = secrets.token_hex(16)
    salt_file.write_text(salt)
    return salt


def ref(value: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}|{value.strip().lower()}".encode()).hexdigest()[:12]


def log_event(log_path: Path, event: str, ts: dt.datetime, **fields) -> dict:
    record = {"event": event, "ts": ts.astimezone(dt.timezone.utc).isoformat(), **fields}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def read_events(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    with open(log_path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def first_built(log_path: Path, deal_ref: str) -> dict | None:
    """Setup time runs from the first build of a deal, including any rebuilds after fixes."""
    built = [e for e in read_events(log_path) if e["event"] == "deal_built" and e["deal_ref"] == deal_ref]
    return built[0] if built else None


def summarize(log_path: Path) -> dict:
    events = read_events(log_path)
    built = [e for e in events if e["event"] == "deal_built"]
    verified = [e for e in events if e["event"] == "deal_verified"]
    deals_by_agent: dict[str, set[str]] = {}
    latest: dict[str, dict] = {}
    for e in built:
        deals_by_agent.setdefault(e["agent_ref"], set()).add(e["deal_ref"])
        latest[e["deal_ref"]] = e
    first_verify: dict[str, dict] = {}
    for e in verified:
        first_verify.setdefault(e["deal_ref"], e)
    minutes = [e["setup_minutes"] for e in first_verify.values() if e.get("setup_minutes") is not None]
    return {
        "deals_built": len(latest),
        "deals_verified": len(first_verify),
        "median_setup_minutes": round(statistics.median(minutes), 1) if minutes else None,
        "unique_agents": len(deals_by_agent),
        "repeat_agents": sum(1 for deals in deals_by_agent.values() if len(deals) >= 2),
        "reminders_queued": sum(e.get("reminders", 0) for e in latest.values()),
    }
