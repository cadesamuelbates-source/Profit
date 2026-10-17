# Concierge prototype: acceptance criteria

Written **before** implementation (2026-10-17). The tests in `tests/` implement these
criteria. If a criterion changes later, record the change and the reason here.
Don't edit a criterion quietly just to make a test pass.

## What this prototype is (and is not)

It's an **operator tool** for the concierge experiment in `docs/05-validation-plan.md`.
The founder types the key terms of an executed purchase contract into a deal sheet.
The tool then produces:

1. a deadline schedule that shows how each date was computed,
2. a calendar file (`.ics`) with alarms,
3. a self-contained, plain-English client timeline page,
4. a reminder outbox (dry run: **nothing is sent**),
5. a verification checklist the operator completes against the signed contract,
6. a metrics event log with no personal data.

It is **not** legal advice and it doesn't read PDFs. It sends nothing and isn't multi-user.
The bundled rule profile is an **EXAMPLE**. It isn't verified against any state's contract form.
Real use requires a profile built from the founder's actual state form and checked by
their broker or an attorney.

## Criteria

### AC1: Deadline arithmetic is correct and explained
Rules: `calendar` counts add N days to the anchor. `business` counts step over
Saturdays, Sundays, and holidays in the profile's holiday set. `roll` (`none`, `forward`,
`backward`) moves a date that falls on a non-business day. Deadlines can anchor to
`effective_date`, `closing_date`, or another deadline. Each deadline carries a
human-readable explanation of its computation.

Hand-computed cases (US federal holidays, observed-date rules):

| # | Rule | Expected |
|---|------|----------|
| 1 | Fri 2026-10-16 + 7 calendar, roll none | Fri 2026-10-23 |
| 2 | Thu 2026-10-22 + 3 calendar, roll forward | Sun 10-25 → **Mon 2026-10-26** |
| 3 | Tue 2026-11-24 + 3 business days | Wed 25, (Thu 26 Thanksgiving skipped), Fri 27, **Mon 2026-11-30** |
| 4 | Tue 2026-12-15 + 10 calendar, roll forward | Fri 12-25 Christmas → **Mon 2026-12-28** |
| 5 | Date Fri 2026-07-03 (observed Independence Day), roll forward | **Mon 2026-07-06** |
| 6 | Closing Mon 2026-11-30, 1 calendar day before, roll backward | Sun 11-29 → **Fri 2026-11-27** |
| 7 | Thu 2027-12-30 + 1 business day | Fri 12-31 is observed New Year's Day 2028 → **Mon 2028-01-03** |
| 8 | Chained: deadline B = deadline A (Fri 2026-10-23) + 2 business days | **Tue 2026-10-27** |

The holiday generator must also match an independent implementation (the `holidays`
PyPI package) for US federal holidays from 2025 to 2030. That cross-check runs only when
the package is installed.

### AC2: Invalid deal sheets are rejected with specific messages
- Closing date before the effective date is an error.
- A negative or non-integer day count is an error that names the field.
- A required term missing for a non-optional deadline is an error that names the term.
  Optional deadlines whose term is missing are skipped. They are listed as "not in this contract".
- An unparseable date is an error.
- A profile anchor that references an unknown deadline is an error.
- A deadline computed **after** closing is a **warning**, not an error. It shows in the checklist.
- A closing date on a non-business day is a warning.

### AC3: The calendar file is valid and importable
- It parses with an independent parser (`icalendar` package, when installed).
- It uses CRLF line endings, and no physical line is longer than 75 octets (RFC 5545 folding).
- Each event has a stable `UID` (same deal + deadline → same UID), `DTSTAMP`, and
  `DTSTART`/`DTEND` in UTC (`...Z`) that equal the local due time converted to UTC.
  It has at least one `VALARM`.
  *Amended 2026-10-17, before any code was written:* the original text said "DTSTART with TZID". RFC 5545 requires a
  matching VTIMEZONE block for every TZID, and generating correct DST rules for any
  IANA zone is error-prone. UTC is unambiguous and every major client handles it.
- Commas, semicolons, backslashes, and newlines in text are escaped.

### AC4: The client timeline is safe and self-contained
- Every user-supplied string is HTML-escaped. A party named `<script>alert(1)</script>`
  appears only in escaped form.
- No `<script>` tags. No external resource URLs (`src=`/`href=` to http(s)) except
  `tel:`/`mailto:` links.
- Deadlines are listed in chronological order. Items owned by the client are marked
  "Your action".
- It includes a wire-fraud warning and a statement that the signed contract governs.

### AC5: The reminder outbox is correct and dry-run only
- Each deadline with an owner gets reminders at the profile's lead times (default:
  2 days before at 09:00 local, and on the day at 09:00 local). They go to the owner
  party and the agent.
- SMS is queued only for parties with `sms_consent: true`. Email is queued only where an
  email exists.
- No reminder is scheduled before `now`. Past reminders are dropped and counted.
- All send times fall within quiet hours (08:00–20:00 local).
- The outbox module imports no networking modules (`socket`, `smtplib`, `urllib`,
  `http`, `requests`).

*Amended 2026-10-17 after the first demo run (these additions make the criteria stricter):* the first build of the sample
deal queued 78 messages for one file and messaged the seller directly on a buyer-side
file. Added rules:
- **Other side's principal:** deadlines owned by the opposite principal (the seller on a
  buyer file, or the buyer on a listing file) go to that side's agent, never to the
  principal. The client page does not list the opposite principal's contact details.
- **One channel per person per reminder:** SMS when the person has a phone number and
  consent; otherwise email.
- **Agent digest:** the agent gets one 08:00 email digest two days before each deadline,
  listing everything due in the next two days. It merges to at most one per day. The agent
  doesn't get one message per deadline.
  *Design change, recorded honestly:* the first digest design (every day a deadline was
  0–2 days away) put the sample file at 46 messages. That failed the "≤ 40 messages
  per file" test, which was written before the result was known. The test stayed as
  written and the design changed. Rationale: an agent needs lead time to prevent a miss,
  and same-day nudges already go to the responsible party. Whether agents want more or
  fewer alerts is an open question for the experiment.
- **One message per person per day:** reminders for one recipient on one day are
  bundled into a single message.
- **Non-rolling weekend deadline:** a deadline that lands on a non-business day under a
  `roll: none` rule is a checklist **warning**.

### AC6: Metrics contain no personal data
- Events are JSON lines: `event`, `ts`, a hashed `deal_ref`, a hashed `agent_ref`, and
  counts or durations only.
- The serialized log contains none of the sample's names, emails, phone numbers,
  or street address.
- `deal_built` → `deal_verified` produces a setup duration in minutes. `summary` reports
  deals built and verified, median setup minutes, unique agents, and repeat agents (≥2 deals).

### AC7: End-to-end CLI run
`python -m c2c build samples/sample-deal.json --out <dir> --now 2026-10-17T09:00`
exits 0 and writes `schedule.json`, `calendar.ics`, `timeline.html`, `outbox.jsonl`, and
`CHECKLIST.md` in under 2 seconds. A bad deal sheet exits non-zero with the error text.

### Not verifiable here (stays open until real use)
- Legal correctness of any state's deadline rules.
- Real delivery of email and SMS. Sending is deliberately absent; it needs a provider,
  10DLC registration, and consent records.
- Real setup time per file with real contracts. Instrumented, but no data yet.
- Whether agents or clients find the page useful. That's measured by the experiment, not by tests.
