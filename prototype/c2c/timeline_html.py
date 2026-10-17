"""Self-contained, plain-English client timeline page (no scripts, no external assets)."""

from __future__ import annotations

import datetime as dt
import re
from html import escape

from .engine import ROLE_LABELS, Schedule, fmt_time

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1c1c1a;--muted:#62625d;--line:#e3e2dd;
--accent:#1f5f8b;--you:#8a4b00;--you-bg:#fff2df;--warn-bg:#fdecea;--warn:#8c1d18}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--card:#1e1e1c;--ink:#f0efea;
--muted:#a8a79f;--line:#33332f;--accent:#7fb6e0;--you:#f3b562;--you-bg:#3a2a12;
--warn-bg:#3b1715;--warn:#f2a29b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,
BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
main{max-width:640px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:1.45rem;line-height:1.25;margin:0 0 4px}
h2{font-size:1.05rem;margin:28px 0 10px}
.sub{color:var(--muted);margin:0;font-size:.92rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.next{margin-top:18px;border-left:4px solid var(--accent)}
.next .when{font-weight:600;color:var(--accent)}
ol{list-style:none;margin:0;padding:0}
li.item{display:grid;grid-template-columns:76px 1fr;gap:12px;padding:14px 0;
border-bottom:1px solid var(--line)}
li.item:last-child{border-bottom:0}
.date{font-weight:600;font-size:.9rem;line-height:1.3}
.date span{display:block;color:var(--muted);font-weight:400}
.title{font-weight:600}
.chip{display:inline-block;font-size:.75rem;padding:1px 8px;border-radius:999px;
border:1px solid var(--line);color:var(--muted);margin-left:6px;vertical-align:1px}
.chip.you{background:var(--you-bg);color:var(--you);border-color:transparent;font-weight:600}
.past{opacity:.55}
.meaning{margin:4px 0 0;color:var(--muted);font-size:.92rem}
.action{margin:6px 0 0;font-size:.92rem}
.warn{background:var(--warn-bg);color:var(--warn);border:0;margin-top:24px}
.contacts p{margin:0 0 8px}
a{color:var(--accent)}
a[href^="tel:"]{white-space:nowrap}
footer{color:var(--muted);font-size:.82rem;margin-top:28px}
"""


def _tel(phone: str) -> str:
    return re.sub(r"[^0-9+]", "", phone or "")


def _valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s<>\"']+@[^@\s<>\"']+\.[A-Za-z]{2,}", value or ""))


def _relative(now: dt.datetime, due: dt.datetime) -> str:
    days = (due.date() - now.astimezone(due.tzinfo).date()).days
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    return f"in {days} days"


def build_timeline_html(schedule: Schedule, now: dt.datetime) -> str:
    deal = schedule.deal
    client = deal["client_role"]
    agent = deal["agent"]
    now_local = now.astimezone(schedule.tz)
    upcoming = [d for d in schedule.deadlines if d.due >= now_local]
    e = escape

    kind = "purchase" if client == "buyer" else "sale"
    parts = [
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
        f"<title>Your home {kind} timeline</title><style>{CSS}</style></head><body><main>",
        f"<h1>Your home {kind} timeline</h1>",
        f"<p class=\"sub\">{e(deal.get('property_address', ''))}</p>",
        f"<p class=\"sub\">Prepared by {e(agent.get('name', ''))}"
        + (f" · {e(agent['brokerage'])}" if agent.get("brokerage") else "")
        + f" · updated {now_local:%b} {now_local.day}, {now_local.year}</p>",
    ]

    if upcoming:
        nxt = upcoming[0]
        yours = nxt.owner == client
        parts.append(
            "<section class=\"card next\" aria-label=\"Next deadline\">"
            f"<div class=\"when\">Next: {e(nxt.label)}</div>"
            f"<div>{nxt.due:%a %b} {nxt.due.day} by {fmt_time(nxt.due)} {nxt.due:%Z}"
            f" ({_relative(now_local, nxt.due)})</div>"
            + (f"<p class=\"action\"><strong>Your action:</strong> {e(nxt.action)}</p>" if yours else "")
            + "</section>"
        )
    else:
        parts.append("<section class=\"card next\"><div class=\"when\">All listed dates have passed.</div></section>")

    parts.append("<h2>Key dates</h2><section class=\"card\"><ol>")
    for d in schedule.deadlines:
        yours = d.owner == client
        owner_label = "Your action" if yours else ROLE_LABELS.get(d.owner, d.owner)
        past = d.due < now_local
        parts.append(
            f"<li class=\"item{' past' if past else ''}\">"
            f"<div class=\"date\">{d.due:%a}<span>{d.due:%b} {d.due.day}</span>"
            f"<span>{fmt_time(d.due)} {d.due:%Z}</span></div>"
            f"<div><div class=\"title\">{e(d.label)}"
            f"<span class=\"chip{' you' if yours else ''}\">{e(owner_label)}</span>"
            + ("<span class=\"chip\">date passed</span>" if past else "")
            + "</div>"
            + (f"<p class=\"meaning\">{e(d.meaning)}</p>" if d.meaning else "")
            + (f"<p class=\"action\"><strong>What to do:</strong> {e(d.action)}</p>" if yours and d.action else "")
            + "</div></li>"
        )
    parts.append("</ol></section>")

    parts.append(
        "<section class=\"card warn\" role=\"note\"><strong>Wire fraud warning.</strong> "
        "Criminals send fake wiring instructions that look like they come from your agent, "
        "lender, or title company. Before sending any money, call the title company at a number "
        "you found independently (not one from an email) and confirm the instructions by voice. "
        "Treat any message that changes wiring instructions as fraud until verified.</section>"
    )

    # The other side's principal is reached through their agent, so they aren't listed.
    other_principal = "seller" if client == "buyer" else "buyer"
    contacts = [("agent", agent)] + [
        (p["role"], p) for p in deal.get("parties", []) if p["role"] not in (client, other_principal)
    ]
    parts.append("<h2>Who to contact</h2><section class=\"card contacts\">")
    for role, person in contacts:
        bits = [f"<strong>{e(ROLE_LABELS.get(role, role))}:</strong> {e(person.get('name', ''))}"]
        if person.get("company"):
            bits.append(e(person["company"]))
        if _tel(person.get("phone", "")):
            bits.append(f"<a href=\"tel:{e(_tel(person['phone']))}\">{e(person['phone'])}</a>")
        if _valid_email(person.get("email", "")):
            bits.append(f"<a href=\"mailto:{e(person['email'])}\">{e(person['email'])}</a>")
        parts.append("<p>" + " · ".join(bits) + "</p>")
    parts.append("</section>")

    parts.append(
        "<footer><p>This page summarizes dates from your signed contract as entered by your "
        "agent's team. <strong>The signed contract and its addenda govern.</strong> If anything "
        f"here differs from your contract, contact {e(agent.get('name', 'your agent'))} right away. "
        "This page is not legal advice.</p></footer></main></body></html>"
    )
    return "".join(parts)
