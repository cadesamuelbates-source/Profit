# Opportunity research: four candidates

Research done 2026-10-17 with web search and direct page reads. Labels:
**[F]** observed fact from the cited source · **[E]** estimate · **[H]** hypothesis (untested).
"Accessed" means the date I read the page. Publication dates are given where the source shows one.

## Research gaps (stated up front)

- **No customer conversations yet.** No interviews were run and none are implied. All demand
  claims below are about *market* evidence, not your customers.
- **Reddit is blocked for automated fetching** in this environment. I didn't work around the
  block, so r/realtors complaints aren't included. Community evidence is limited to vendor pages,
  association case studies, and app-store listings.
- **No private analytics.** I have no Roblox per-game benchmarks, Roblox ad cost-per-play data
  (Roblox doesn't publish it), or US survey data that isolates "status updates" as a complaint.
- Several prices come from third-party aggregators. Each is marked, so you can verify it before relying on it.

---

## A. Roblox: "Fixer-Upper Friends", a co-op renovate-and-flip tycoon

**Concept [H].** Two to four friends buy a run-down house, split repair mini-jobs (demolition,
paint, plumbing), stage it, and sell to buyers whose tastes vary. Each round takes about 10–15
minutes. Coins unlock tools, bigger houses, and decor; there's a showcase home friends can visit.
Monetization is kid-appropriate: fixed-price cosmetic decor packs and one optional game pass for
extra save slots. There are **no paid random items, no paid trading, and no countdown pressure**.
Everything that affects gameplay can be earned for free.

**Platform facts**

| Fact | Source |
|------|--------|
| [F] The standard DevEx rate is **$0.0038 per Earned Robux** (it was $0.0035 before Sep 5, 2025). Cash-out requires 30,000 Earned Robux and age 13+ | [Roblox DevEx docs](https://create.roblox.com/docs/production/monetization/developer-exchange), accessed 2026-10-17 |
| [F] There's a higher **$0.0054 rate** for purchases by U.S. players age-verified as 18+ | Same page. Announcement covered by [Tubefilter](https://www.tubefilter.com/?p=192104) |
| [F] "Creators generally earn **70%** of anything they sell in Robux in their game." The pass and developer-product pages give no separate percentage | [Earn on Roblox](https://create.roblox.com/docs/production/earn-on-roblox), accessed 2026-10-17 |
| [F] Paid random items need numerical odds disclosed before purchase. Creators must check `PolicyService` → `ArePaidRandomItemsRestricted` and give ineligible users an alternative path | [Paid random items policy](https://create.roblox.com/docs/production/monetization/paid-random-items), accessed 2026-10-17 |
| [F] Brazil (2026): users under 18 can't access paid random items, and games that don't use PolicyService are blocked for them | [Roblox Help, Brazil Digital ECA](https://en.help.roblox.com/hc/cs/articles/48706630819476-Brazil-Digital-ECA-Updates) |
| [F] Creator Rewards (engagement-based payouts) replaced Premium/Engagement Payouts on **Jul 24, 2025**, with a 60-day hold | [Roblox 10-Q, Q2 2026](https://www.sec.gov/Archives/edgar/data/0001315098/000162828026051082/rblx-20260630.htm); [DevForum announcement](https://devforum.roblox.com/t/introducing-creator-rewards-earn-more-by-growing-the-community/3777628) |
| [F] Discovery (June 2026): "Recommended for You" now weighs a **28-day** behavior window and favors retention, co-play, and spending | [Roblox newsroom, Jun 2026](https://about.roblox.com/newsroom/2026/06/optimizing-discovery-great-games-reach-millions-players-roblox) |
| [F] Ads Manager publishes **no minimum budget or cost-per-play**. Card payment requires age 18+ | [Ads Manager docs](https://create.roblox.com/docs/production/promotion/sponsoring-experiences), accessed 2026-10-17 |

**Market facts**

- [F] Q2 2026: 123M daily active users (+10% YoY, down from the Q3 2025 peak) and $1.6B bookings
  (+8%). Roblox said the miss came from engagement shifting away from "high monetizing,
  2025-vintage viral games" ([Shacknews, Jul 31 2026](https://www.shacknews.com/article/150208/roblox-daus-grew-10-percent-yoy);
  [Q2 2026 supplemental PDF](https://s27.q4cdn.com/984876518/files/doc_financials/2026/q2/Roblox-Q2-2026-Supplemental-Materials.pdf)).
- [F] **The typical creator earns little.** The median DevEx payout was **$1,440/yr** and the top
  1,000 averaged $980k, for Jun 2024–Jul 2025 ([Game World Observer, Sep 8 2025](https://gameworldobserver.com/2025/09/08/how-much-top-developers-earn-in-roblox-official-data)).
  In 2025 the top 1,000 averaged about $1.3M out of roughly $1.5B paid to creators
  ([Sherwood](https://www.sherwood.news/business/the-top-1-000-roblox-creators-earned-an-average-of-usd1-3-million-last-year/)).
- **Success story [F]:** *Grow a Garden*, reportedly built in days by a 16-year-old, peaked at 22.3M
  concurrent players on Aug 23, 2025 ([Wikipedia](https://en.wikipedia.org/wiki/Grow_a_Garden)).
  It lost the record to *Steal a Brainrot* within weeks.
- **Failure pattern [E]:** clones of a hit flood discovery within weeks. The 2026 bookings shift
  shows that even hits' monetization fades. Most games never reach the 30,000 Earned Robux needed
  to cash out once (median payout above).

**Assessment.** Demand for fun is enormous, but outcomes follow a power law. You have no
evidence-backed edge in game design, art, or player audience. Your real-estate knowledge only adds
theme. Reaching $10k/month needs about 3.76M Robux of in-game spending a month, or tens of
thousands to 250k daily players (see [04-financial-model.md](04-financial-model.md) §6). This is
a reasonable *hobby* bet, not the business bet.

---

## B. Trading: two separate economics

### B1. Risking your own capital on a bot

- [F] Of Brazilian futures day traders who persisted 300+ days, **97% lost money**. Only about 1.1%
  earned more than the minimum wage ([Chague, De-Losso & Giovannetti, "Day Trading for a Living?"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101)).
- [F] Quantopian, a VC-funded platform for crowdsourced trading strategies, returned investors'
  money in Feb 2020 "due to the underperformance of its investment strategies" and shut down in
  Nov 2020 ([Wikipedia](https://en.wikipedia.org/wiki/Quantopian), last edited Aug 2026). Its own
  2016 study ("All That Glitters Is Not Gold") found backtest metrics had "little value in
  predicting out of sample performance," according to [eFinancialCareers](https://www.efinancialcareers.com/news/2020/11/quantopian-shutdown).
- [F] Tools are cheap: Alpaca paper trading is free, and full real-time market data costs $99/mo
  (Algo Trader Plus) ([Alpaca docs](https://docs.alpaca.markets/us/docs/about-market-data-api)).
- **Economics [E]:** a bot earns only its *excess* return over a passive benchmark. $120k/yr at
  a 3% edge needs $4M of capital (model §6). **Without large capital this isn't an income path,
  even if the strategy works.** Keep it, at most, as a paper-trading research hobby with live
  trading off.

### B2. Selling trading software: "Backtest Reality Check" [H]

A tool for retail systematic traders. It re-runs a strategy with walk-forward splits, realistic
fees, spread, and slippage, and adjusts for testing many strategy variants. It then gives a
plain-English verdict on whether the edge survives. It sells *analysis software*, not signals.

- [F] Retail traders do pay for analytics: TradeZella ~$29–49/mo, TraderSync $29.95–79.95/mo,
  Edgewonk ~$169–197/yr. These are vendor and third-party figures from 2026
  ([Tradervue roundup](https://www.tradervue.com/blog/best-trading-journal)).
- [F] **Category risks:** the FTC's case against RagingBull, which alleged $137M in revenue built
  on deceptive earnings claims, settled for $2.425M in Mar 2022
  ([FTC](https://www.consumer.ftc.gov/consumer-alerts/2022/03/investment-trading-operation-will-pay-millions-empty-promises)).
  The 3Commas API-key leak in Dec 2022 was tied to $14.8M+ in losses
  ([BleepingComputer](https://www.bleepingcomputer.com/news/security/crypto-platform-3commas-admits-hackers-stole-api-keys)).
  The investment-adviser "publisher exclusion" (*Lowe v. SEC*, 1985) covers impersonal
  publications. Commentators warn that auto-trading platforms leaning on it should be careful
  ([Greenberg Traurig, Aug 2024](https://www.gtlaw.com/de/insights/2024/8/no-need-for-seeking-alpha-to-seek-registration)).
- [E] The customers are mostly unprofitable traders, who churn as they quit. Telling people their
  strategy doesn't work is valuable but hard to sell [H]. You have no trading-community audience.

---

## C. Real-estate niche tool: "Contract-to-Close Desk" (provisional winner)

**Offer [H].** For agents closing 12+ sides a year who don't use a full-service transaction
coordinator (TC). Within 2 business hours of receiving the signed contract, you enter its terms
and **check every date against the contract**. You then deliver a client timeline page, calendar
invites, a sensible reminder schedule for the client, lender, title, and the other side's agent,
and a digest for the agent. Price: **$129 per file**. You don't give legal advice, negotiate, or
keep the compliance file.

**Why this job: the money already flows**

| Evidence | Source |
|----------|--------|
| [F] Human TCs publish **$300–$500 per side** (most $375–400). There's no official survey of TC pricing | [HousingWire](https://www.housingwire.com/articles/real-estate-file-ops-costs/); [Paperless Pipeline](https://www.paperlesspipeline.com/blog/how-to-start-a-real-estate-transaction-coordinator-business) |
| [F] The AI TC **ListedKit charges $14.99 per buyer file** ($11 at volume). It reads contracts, builds timelines, and drafts emails and texts. First file free, no monthly fee | [listedkit.com/pricing](https://www.listedkit.com/pricing), accessed 2026-10-17 |
| [F] Transactly's Elite plan is ~$339–379/mo (third-party listing) | [PricingSaaS](https://pricingsaas.com/companies/transactly) |
| [F] Client-facing trackers exist: CloseSimple (aimed at title companies), Lofty's client portal, Nekst Client (free iPad app, 1 rating), Rayse | [CloseSimple](https://www.closesimple.com/the-pizza-tracker-for-title); [Nekst Client, App Store](https://apps.apple.com/us/app/nekst-client/id6756778747) |
| [F] Missed deadlines bring regulator penalties. In a Virginia REALTORS case study (Mar 2026, names fictitious), a licensee was fined $550 plus 3 hours of education for failing to make sure earnest money arrived within 5 days | [Virginia REALTORS](https://virginiarealtors.org/?p=3183505) |
| [F] Since Aug 17, 2024, buyer agents need a **written agreement before touring**, and compensation offers are off the MLS. That's more paperwork per client | [NAR, "What the settlement means"](https://www.nar.realtor/the-facts/what-the-nar-settlement-means-for-home-buyers-and-sellers) |

**Market size and headwinds**

- [F] The typical agent had **9 transaction sides in 2025**, with median gross income of **$59,200**.
  Membership was **1,439,163** on June 18, 2026, down from 1,463,352 a year earlier
  ([NAR, Jun 25 2026](https://www.nar.realtor/news/real-estate-news/even-in-a-tougher-market-realtors-are-holding-their-ground)).
  The prior year reported 10 transactions in 2024 and $58,100
  ([NAR release, Aug 6 2025](https://www.nar.realtor/press-releases/realtors-show-strong-commitment-to-profession-amid-market-headwinds-new-nar-report-finds)).
  Membership peaked at about 1.6M in Oct 2022 (secondary reporting).
- [F] 2025 existing-home sales were **4.06M**, about the lowest since 1995
  ([Inman, Jan 14 2026](https://www.inman.com/2026/01/14/2025-existing-home-sales-miss-2024-pace-by-razor-thin-1k-margin/)).
- [E] Fewer deals per agent means less per-agent spending capacity and more agents leaving
  (churn). The target segment (12+ sides) is a minority of agents.
- [F, weak] UK surveys put poor communication at the top of complaints about agents (~20–23%)
  ([Estate Agent Today](https://www.estateagenttoday.co.uk/1434-naea-most-buyers-and-sellers-have-agent-problems)).
  This is UK data, partly from 2014, so its relevance to US agents is unverified.

**Competition and why this could fail [E]**

- The space is crowded at both ends: ListedKit is cheap self-serve AI, and human TCs offer full
  service. **The middle tier may not exist**: agents might either do it themselves for free or
  hand off the whole file.
- Brokerages, title companies, and lenders give agents free tools, which caps willingness to pay.
- ListedKit or a CRM could add a client page tomorrow. Your moat is service quality, local
  contract expertise, and relationships, not software.
- **Unsuccessful example:** OnTheMarket closed its lettings-software arm in Jun 2025 after a
  strategic review ([The Negotiator](https://thenegotiator.co.uk/onthemarket-closes-lettings-software-arm-in-surprise-move)).
  That's UK-specific, but it shows agent software being cut even inside an established company.

**Your advantage [H, depends on question 1]:** you can reach buyers directly and you know the
local contract form. Those are the two things a remote software vendor lacks.

---

## D. Property-tax appeal service with software support (real-estate-adjacent consumer offer)

**Offer [H].** Pull public assessor data, pick comparable sales, prepare the evidence packet,
and file the protest for homeowners on contingency. Start with your past clients.

- [F] Ownwell charges **25–35% of actual savings**, nothing if there are no savings, in 9 states. It
  has a 4.7 Google rating from 3,000+ reviews ([Ownwell FAQ](https://www.ownwell.com/faqs), accessed 2026-10-17).
  That's direct evidence of willingness to pay under a contingency model.
- [F] Texas requires registration for paid property-tax consulting (2,216 licensees in FY24). **Real-estate brokers and
  salespeople are exempt when the work is limited to single-family homes, farms, or ranches**
  ([TDLR, PTC at a Glance](https://www.tdlr.texas.gov/media/pdf/PTC%20at%20a%20Glance.pdf)).
  Consultants may not promise outcomes.
- [E] Downsides: it's seasonal (one protest window a year), rules differ county by county, Ownwell
  and local firms are funded or established, and the work is labor-heavy without county-specific
  automation. About 1,100 signed homeowners a year would be needed for $10k/month (model §6).

**Assessment.** Willingness to pay is strong, but whether it's viable depends on your state. If
you're a Texas agent with a past-client list of 300+, it's a strong *second* experiment for the
next protest season.
