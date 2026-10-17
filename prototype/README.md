# c2c: Contract-to-Close Desk operator tool (validation prototype)

The concierge toolkit for the experiment in `docs/05-validation-plan.md`. It's Python 3.11+
standard library only, with no network access and **no message sending**.

```bash
cd prototype
# Build a packet from a deal sheet (dates checked against the profile's rules)
python3 -m c2c build samples/sample-deal.json --out /tmp/packet --now 2026-10-17T09:00
# After checking every line of CHECKLIST.md against the signed contract:
python3 -m c2c verify /tmp/packet           # records setup minutes (no personal data)
python3 -m c2c summary                      # deals, setup time, repeat agents
python3 -m c2c funnel ../validation/tracker.csv --thresholds ../validation/thresholds.json

python3 -m unittest discover -s tests -t tests   # 63 tests
```

Optional independent cross-checks run when `holidays` and `icalendar` are installed:
`pip install holidays icalendar`. They compare our federal-holiday logic and calendar output with
third-party implementations.

**Outputs per deal:** `schedule.json`, `calendar.ics`, `timeline.html` (self-contained client
page; print to PDF from any browser), `outbox.jsonl` (reminder plan, dry run), and `CHECKLIST.md`
(the human check against the contract).

**Before real use:** replace `profiles/example-generic.json` with a profile for your state's
current contract form, reviewed by your broker or an attorney. The example is labeled EXAMPLE
on purpose. Its rules are illustrative.

`samples/demo-packet/` holds the output for the fictional sample deal, for showing to agents.

Acceptance criteria (written before the code, amendments recorded): [ACCEPTANCE.md](ACCEPTANCE.md).
