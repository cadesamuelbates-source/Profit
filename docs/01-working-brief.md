# Working brief: the professional standard

## What an excellent founder would do that the original request overlooks

1. **Start from a buyer and a job they already pay for, not a product category.** The three
   candidates are different kinds of bet. A Roblox game is a hits-driven entertainment bet. A
   trading bot on your own money is an *investment*, not a business, and its income scales with
   capital, not effort. Real-estate software is a B2B sale. Comparing them only makes sense
   through who pays, how much, and how you reach them.
2. **Treat distribution as half the product.** For a solo founder without an audience, the
   scarcest asset is access to buyers who'll take your call. You may have that in real estate.
   You almost certainly don't have it with Roblox players or traders.
3. **Price against money already being spent.** Agents already pay human transaction
   coordinators $300–500 per file, while AI tools sell for about $15 per file. A new offer has to
   find room inside that range.
4. **Sell before you build.** Deliver the outcome by hand (a "concierge" test) to collect real
   payments and timing data. Write software only where it cuts labor or errors.
5. **Fix pass/fail thresholds before collecting data, and count only behavior.** Compliments,
   clicks, signups, promises, payments, and repeat payments are separate signals. Only payments
   and repeat payments show willingness to pay.
6. **Check rules before building.** That means brokerage policy, state license law, client-data
   handling, SMS consent and registration, Roblox's youth-monetization rules, and SEC/CFTC limits
   on selling trading advice.
7. **Work backward from the target.** $10,000/month of profit implies a specific number of
   customers, sales, and hours. If that number is impossible for one person, change the plan
   before building.
8. **Compare against your fallback.** Working those same hours at a market rate is the
   benchmark. Report profit both before and after paying yourself.

## Raw evidence they'd start from

- Your own last 10 transactions: the email threads, the deadlines that came closest to being
  missed, and the time spent chasing lenders, title, and clients.
- Your MLS or brokerage production data, to find agents who closed 12+ sides in 12 months and
  how many of them use a transaction coordinator.
- What agents spend now: TC invoices, software subscriptions, and brokerage-provided tools.
- Competitor pricing pages, app-store listings, and reviews. Regulator and association case studies.
- Platform documentation (Roblox Creator Docs, broker APIs) and public filings (Roblox
  10-K/10-Q), not blog summaries.

## Methods and tools

| Need | Method | Tool in this repo |
|------|--------|-------------------|
| Is the problem real? | Problem interviews that ask about past behavior, not opinions about the idea ("Mom Test" style) | `validation/interview-script.md` |
| Will they pay? | Concierge pre-sale with a real invoice, paid on delivery | `validation/offer.md`, `prototype/` |
| Do they come back? | Repeat purchase at full price within 60 days | `validation/tracker.csv` + `c2c funnel` |
| Can it be profitable? | Unit economics, ramp, $10k backsolve, sensitivity | `model/financial_model.py` |
| No goal-post moving | Thresholds fixed in advance, with a SHA-256 hash | `validation/thresholds.json` |
| Is the output correct? | Acceptance criteria written before code, independent cross-checks | `prototype/ACCEPTANCE.md`, `prototype/tests/` |

## Outside evidence that would show the product works and the business is viable

Each of these comes from the outside world, not from another AI agreeing:

- **Payments:** at least 4 of 40 qualified agents pay $129 for a real file within 30 days.
- **Repeat:** at least 2 of those payers pay again within 60 days.
- **Delivery cost:** median setup-and-verification time of 30 minutes or less, from the instrumented log.
- **Quality:** zero date errors reach a client. Each date is checked against the signed contract.
- **Later, at scale:** monthly churn under 5% for 3+ months, unprompted referrals, and acquisition
  cost recovered within 2 months.

The rest of this repo carries out this brief.
