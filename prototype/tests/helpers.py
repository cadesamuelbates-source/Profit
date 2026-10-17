import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DEAL = ROOT / "samples" / "sample-deal.json"
EXAMPLE_PROFILE = ROOT / "profiles" / "example-generic.json"


def sample_deal() -> dict:
    return json.loads(SAMPLE_DEAL.read_text())


def example_profile() -> dict:
    return json.loads(EXAMPLE_PROFILE.read_text())


def one_rule_profile(**rule) -> dict:
    base = {"key": "d", "label": "Deadline", "anchor": "effective_date", "owner": "buyer",
            "days": {"fixed": 0}, "count": "calendar", "roll": "none"}
    base.update(rule)
    return {"profile_id": "test", "timezone": "America/Chicago", "deadlines": [base]}


def minimal_deal(effective: str, closing: str, **terms) -> dict:
    return {
        "deal_id": "T-1",
        "client_role": "buyer",
        "effective_date": effective,
        "closing_date": closing,
        "terms": terms,
        "agent": {"name": "Agent Test"},
        "parties": [],
    }


def deep(d: dict) -> dict:
    return copy.deepcopy(d)
