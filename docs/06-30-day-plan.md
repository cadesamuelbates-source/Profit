# 30-day plan with continue/stop gates

Assumes about 15 h/week (A3) and ≤ $100 cash (A2). Each gate depends on observed behavior,
never on effort spent.

## Days 1–3: unblock

- Answer the three questions in [00-questions-and-assumptions.md](00-questions-and-assumptions.md).
- **Ask your broker** whether you may offer this to other agents and handle their client data (A5).
- Build the **state rule profile** from your current state purchase contract. Use
  `prototype/profiles/example-generic.json` as the template: one entry per deadline paragraph,
  covering calendar vs. business days, weekend/holiday rolling, and the due time. Have your broker
  or an attorney review it. *Ask before paying for a review.*
- Pull your list of 40+ qualifying agents (12+ sides, no full-service TC) into `tracker.csv`.

**Gate 0:** without broker approval and a reviewed profile, don't run real files. Do interviews only.

## Days 4–7: calibrate on practice files

- Run 2–3 **practice files** using real past contracts (yours or a friendly agent's, with
  permission). Time each one with `c2c build` → `c2c verify`.
- Hold 5–8 problem interviews (script: `validation/interview-script.md`).

**Gate 1 (day 7):**

| Result | Action |
|---|---|
| Every computed date matched the contract | Continue |
| Any mismatch | Fix the profile and re-test before outreach |
| Practice setup > 45 min | Simplify the deal sheet first (time is a CONTINUE criterion) |

## Days 8–21: sell and deliver

- Contact agents one at a time through the channels in `validation/outreach-messages.md`, up to 20
  or more qualified contacts. Deliver every accepted file the same day and invoice on delivery.
- Log every stage in `tracker.csv` the same day. Run `c2c funnel` weekly.

**Gate 2 (day 21):** this is an early warning, not a stop. If 0 of 20 have paid *and* fewer than
25% of interviewed agents rank this a top-3 problem, write down what you heard. Still finish all
40 contacts. The STOP rule needs the full sample.

## Days 22–30: finish the sample

- Reach 40 qualified contacts. Collect payments. Paste the `c2c funnel` output into
  `validation/results-log.md`.

**Gate 3 (day 30), applied mechanically by `c2c funnel`:**

| Decision | Next 30 days |
|---|---|
| **CONTINUE** (≥ 4 paid, ≥ 2 repeat, setup ≤ 30 min, 0 errors) | Build v1: hosted app with login; contract-PDF date extraction *with* human checking; email/SMS sending through a provider, with consent and 10DLC registration; Stripe invoicing. Start a scalable channel test (one team or brokerage deal). |
| **PENDING** (≥ 4 paid, repeat window still open) | Keep delivering. Don't build yet. Decide when the repeat window closes. |
| **ITERATE** | One more round of 40 with **one** change written into a new thresholds file *before* contacting anyone: (a) target teams and independent TCs, or (b) $79 per file |
| **STOP** | Stop this offer. Reread the interview notes for the most-cited pain that people *already pay for*. If you're eligible (e.g., a Texas agent with a past-client list), prepare the property-tax concierge test for the next protest season. |

## What not to do in these 30 days

Don't build the hosted app, add AI contract parsing, buy ads, register a company or SMS campaign,
or buy insurance. Nothing gets bought or turned on until a gate calls for it and you approve it.
