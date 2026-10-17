# Validation plan: test the assumption most likely to kill the business

## Riskiest assumption

> **Agents who close 12+ sides a year will pay about $129 per file for a human-checked deadline
> schedule plus client-communication setup, and will pay again on their next file.**

Why this assumption and not another:

- **Software feasibility isn't the risk.** The prototype already computes, explains, and renders
  everything, with 63 passing tests.
- **The likely failure is the squeezed middle.** Agents may do it themselves for free, pay $15 for
  self-serve AI (ListedKit), or hand off the whole file for $300–500. If a middle tier doesn't
  exist, nothing downstream matters.
- **The model's biggest levers are acquisition and repeat use** (model §4). One payment without a
  repeat proves little.

Secondary risks, measured in the same test:

- **R2:** setup time is 30 minutes or less per file. Otherwise margins collapse (model §4: 90 minutes costs about $1.7k/month at month 24).
- **R3:** no date errors reach a client. Accuracy is the whole promise.

## Experiment: concierge pre-sale on live files

| Element | Definition (fixed in advance) |
|---|---|
| **Audience** | Licensed agents in your market who closed **12+ sides in the last 12 months** and **don't use a paid full-service TC on most files**. Qualify each one by asking before you pitch. |
| **Offer** | [validation/offer.md](../validation/offer.md): $129 per file, invoiced on delivery, due in 7 days; "if it isn't useful, don't pay." Works on a deal **already under contract** with 10+ days to closing, so agents don't have to wait for a new deal. |
| **Primary metric** | **Distinct agents whose payment cleared** (not refunded) within 30 days of first contact |
| **Secondary metrics** | Repeat paid agents within 60 days of first payment. Median setup minutes (instrumented: `c2c build` → `c2c verify`). Client-visible date errors. Problem-interview pain share. Each funnel stage counted separately. |
| **Sample** | **40 qualified agents** contacted one-to-one. A STOP can't be declared before 40. A CONTINUE can come earlier because its thresholds are absolute counts. |
| **Duration** | 30 days to first payment; 60-day repeat window after each payment |
| **Cost limit** | ≤ **$100 cash** and ≤ **30 founder hours**, not counting paid delivery time. No ads. |
| **CONTINUE** | **≥ 4 paying agents** AND **≥ 2 repeat payers** AND **median setup ≤ 30 min** AND **0** client-visible date errors |
| **ITERATE** | Anything between: 1–3 payers, or not enough repeat payers, or slow setup. One more round of 40 with **one** change chosen in advance (see 03-decision.md). |
| **STOP** | 0 payers after 40 qualified contacts; OR any date error that reaches a client; OR fewer than 4 payers *and* under 25% of 15+ interviewed agents ranking this a top-3 time sink |

Machine-readable copy: [validation/thresholds.json](../validation/thresholds.json).
SHA-256 at pre-registration (2026-10-17):
`a2e5e1977fae2f94b0d818df5c21fa78bc00b7f429d91003171ad5ba389847e8`.
The command `python -m c2c funnel` prints the current hash, so any later edit shows up.

### Why these thresholds mean something

- **4 of 40 (10%) from your warmest network.** The model needs about 106 active agents for $10k/month
  in the base case. Cold outreach usually converts worse than warm [E]. Under 5% warm conversion
  would mean thousands of cold contacts in one market. With the pass line at 4 payers, a true rate
  of 5% passes only 14% of the time, while a true rate of 15% passes 87% of the time (model §5).
- **2 repeat payers.** Repeat use at full price is the strongest available evidence that the
  value is real and not a favor to you. Churn and acquisition dominate profit (model §4).
- **Setup ≤ 30 minutes.** At $129, delivery above about 50 minutes per file makes paying for help
  uneconomic (model §1–4).
- **Zero client-visible errors.** One wrong date that a client relies on can cost earnest money,
  so the promise has to hold from day one.

### Evidence ladder: each rung is counted separately

| Rung | Counts as | Doesn't count as |
|---|---|---|
| Compliment ("this is cool") | `compliment_only` | interest, intent, or demand |
| Viewed the demo | `viewed_demo` | a signup |
| Sent a deal sheet or contract | `submitted_deal_sheet` | a commitment to pay |
| Wrote "yes, I'll pay $129" | `written_commitment` | a payment |
| **Payment cleared, not refunded** | `first_paid_on` + `revenue_usd` | repeat use |
| **Second paid file** | `second_paid_on` | product-market fit; that needs months |

## Validation assets (ready now)

| Asset | Purpose |
|---|---|
| [validation/interview-script.md](../validation/interview-script.md) | 15-minute problem interview about past behavior, then demo and offer |
| [validation/offer.md](../validation/offer.md) | One-page offer with scope, price, exclusions, and data handling |
| [validation/outreach-messages.md](../validation/outreach-messages.md) | First-10-customers channels and exact messages (**drafts. Nothing has been sent.**) |
| [validation/tracker.csv](../validation/tracker.csv) | Funnel ledger with one row per agent |
| [validation/results-log.md](../validation/results-log.md) | Dated log of what happened. **Currently empty: no data has been collected.** |
| [prototype/samples/demo-packet/](../prototype/samples/demo-packet/) | Demo output from a fictional deal: client page, calendar, checklist, outbox |
| `prototype/` (`python -m c2c ...`) | Operator tool for real files, plus setup-time instrumentation and the funnel decision |

## Exact dependencies (what I can't do from here)

1. **Your answers to the three questions**, especially your state, which determines the contract
   form and deadline rules.
2. **A state rule profile** built from your state's current purchase contract and checked by your
   broker or an attorney. The bundled profile is an explicitly labeled EXAMPLE. Using it on a real
   file would be wrong.
3. **Your broker's OK** for a side business that serves other agents and handles client data.
4. **Real agents and real elapsed time:** 40 conversations and 30–60 days. These can't be simulated,
   and no result will be recorded until it happens.
5. **Your approval before** sending any outreach, spending money (insurance quote, domain, SMS
   registration), or turning on any automated sending.
