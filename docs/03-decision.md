# Decision: provisional winner and what would change it

## Comparison

Ratings are relative judgments (High / Med / Low), each backed by evidence in
[02-opportunity-research.md](02-opportunity-research.md). These aren't probabilities.

| Criterion | A. Roblox co-op tycoon | B1. Bot on own capital | B2. Backtest-check software | **C. Contract-to-Close Desk** | D. Property-tax appeals |
|---|---|---|---|---|---|
| Evidence of demand & willingness to pay | High demand for fun; **Low** for a new solo game (median payout $1,440/yr) | n/a (no customer); edge evidence negative (97% of persistent day traders lost) | Med: journals sell at $15–80/mo | **Med–High**: agents pay TCs $300–500/file; AI at $15/file | **High**: 25–35% contingency, Ownwell at scale |
| Your advantage & customer access | **Low**: no audience, no game portfolio known | Low: needs capital you don't have | **Low**: no trader audience | **High if question 1 confirms**: direct access + local contract knowledge | Med: past clients; legal eligibility depends on state |
| Time/cost to a useful first version | Med: 4–8 weeks for a graybox prototype; ad spend for players | Low cost, but only paper trading is responsible | Med: 4–6 weeks | **Low**: concierge works now; prototype built | Low: concierge possible, but must wait for the protest season |
| Distribution, competition, switching/return | Algorithm-gated; clones within weeks | n/a | Crowded; heavy churn | Crowded at both ends; **every new file is a reason to return** | Funded rivals; return once a year |
| Ongoing costs, platform dependence, downside | Total dependence on Roblox's algorithm and rules; youth-safety obligations | Capital loss; leaked keys | FTC and adviser-law exposure if marketing slips | Liability for date errors; reliance on brokerage policy and MLS | Licensing; seasonal labor spikes |
| Repeatable profit & expansion | Hits-driven | Scales with capital only | Subscription, but churn-heavy | Per-file revenue; expand to teams, brokerages, TCs, other states | County-by-county expansion |

## Provisional recommendation: **C. Contract-to-Close Desk**, concierge first

The software isn't new. ListedKit, CloseSimple, Nekst Client, and others exist. It's the
choice because:

1. **Money already moves for this job.** It ranges from $15 (AI) to $300–500 (human TC) per file,
   so you're competing for an existing budget, not creating one.
2. **Your scarcest asset applies here.** You can reach the buyer directly, which you can't with
   Roblox players or traders. (This depends on question 1.)
3. **It's the cheapest decisive test.** A real invoice paid by a real agent within 30 days costs
   ≤ $100 and about 30 hours.
4. **It recurs year-round with each file**, unlike property-tax appeals, and has a small downside.

**Not recommended now:** risking your own capital on a trading bot, because it needs millions of
capital to reach $10k/month even with a real edge (model §6). Building a Roblox game as the
*business* bet is also out, though it's fine as a hobby.

## What would change this choice

| Evidence | New choice |
|---|---|
| Question 1: you **can't reach 40 qualifying agents** (you aren't in a brokerage, or your market is tiny) | The access advantage is gone. Rerun the comparison. D (if eligible) or B2 come next. |
| Question 1: **Texas agent with 300+ past clients** | Run D as a second concierge test before the next protest deadline |
| Interviews: **50% or more of target agents already have a TC or brokerage tool they like** | Stop C before selling. Re-mine interview notes for the most-cited *paid* pain |
| Experiment returns **STOP** (0 of 40 paid, or a date error reached a client) | Stop C as designed. Don't argue with the threshold |
| Experiment returns **ITERATE** | One more round with one pre-registered change: target teams and independent TCs (more files per account) *or* a $79 price |
| You have a **shipped game or a game-dev portfolio** and 20+ h/week | A becomes a reasonable side bet with a 2-week playable test (D1/D7 retention). Still not the primary business |
| You have **$1M+ investable** and want automation | B1 as a paper-traded research program (walk-forward, untouched holdout), live trading off. That's an investment decision, not a business |

## The honest ceiling

The model (§3) shows $10k/month in the base case needs about **106 active paying agents**, and
about 5 new ones every month just to replace churn. A solo founder signing agents one at a time
levels off near 100. Reaching the target needs a channel that scales: team or brokerage
agreements, referral loops, or a white-label deal. That's a phase-2 question, but it's why the
experiment measures repeat use and sales effort, not just one payment.
