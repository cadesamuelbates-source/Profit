"""Transparent financial model for the provisional winner and the alternatives.

Run:  python3 model/financial_model.py
Writes docs/04-financial-model.md and model/output/ramp_<scenario>.csv.

Every input is labeled:
  FACT       a published price or rule (source in docs/02-opportunity-research.md)
  ESTIMATE   a judgment informed by public benchmarks; replace with real data
  HYPOTHESIS an untested belief; the validation experiment exists to test it
Nothing here is a forecast. It's a calculator for checking whether the plan can
work and which assumptions matter most.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = 10_000  # hypothetical monthly operating-profit target, USD


@dataclass(frozen=True)
class Scenario:
    name: str
    price_per_file: float          # HYPOTHESIS: experiment tests $129
    refund_writeoff_rate: float    # ESTIMATE: refunds, unpaid invoices, cancelled deals
    files_per_agent_month: float   # ESTIMATE: target agents close >= 12 sides/yr
    agent_monthly_churn: float     # ESTIMATE: SMB tools 3-8%/mo; agents also leave the business
    new_agents_per_month: float    # HYPOTHESIS: founder-led sales capacity
    sales_hours_per_new_agent: float  # ESTIMATE
    cash_cac_per_new_agent: float  # ESTIMATE: coffees, office meetings, small events
    delivery_minutes_per_file: float  # HYPOTHESIS: setup + verification + exceptions
    founder_hours_capacity: float  # ASSUMPTION A3 (unconfirmed): hours/month available
    outsourced_rate_per_hour: float = 35.0  # ESTIMATE: contract TC/VA hourly cost
    founder_value_per_hour: float = 40.0    # ASSUMPTION: what your time is worth elsewhere
    admin_hours_month: float = 8.0          # ESTIMATE: bookkeeping, support inbox, fixes

    # Variable costs per file
    card_fee_pct: float = 0.029   # FACT: Stripe US online card rate (third-party read, 2026)
    card_fee_fixed: float = 0.30  # FACT: same source
    invoicing_pct: float = 0.004  # ESTIMATE: Stripe Invoicing fee; verify on your account
    sms_segments_per_file: float = 35   # ESTIMATE from demo outbox (22 segments, one consenting buyer)
    cost_per_sms_segment: float = 0.0128  # FACT-ish: Twilio $0.0083 + carrier fees (third-party calc, Sep 2026)
    email_cost_per_file: float = 0.05     # ESTIMATE

    # Fixed monthly costs
    hosting: float = 25.0          # ESTIMATE: small app host + database
    software: float = 45.0         # ESTIMATE: email service, workspace, domain, e-sign
    sms_fixed: float = 12.0        # FACT-ish: 10DLC campaign (~$10) + number ($1.15)
    insurance: float = 100.0       # ESTIMATE: E&O / tech liability; get a real quote
    bookkeeping: float = 30.0      # ESTIMATE

    @property
    def fixed_monthly(self) -> float:
        return self.hosting + self.software + self.sms_fixed + self.insurance + self.bookkeeping

    @property
    def variable_cost_per_file(self) -> float:
        collected = self.price_per_file * (1 - self.refund_writeoff_rate)
        return (collected * (self.card_fee_pct + self.invoicing_pct) + self.card_fee_fixed
                + self.sms_segments_per_file * self.cost_per_sms_segment + self.email_cost_per_file)

    @property
    def contribution_per_file(self) -> float:
        """Cash per file after refunds and variable costs, before anyone's labor."""
        return self.price_per_file * (1 - self.refund_writeoff_rate) - self.variable_cost_per_file

    @property
    def delivery_hours_per_file(self) -> float:
        return self.delivery_minutes_per_file / 60


SCENARIOS = [
    Scenario("conservative", price_per_file=99, refund_writeoff_rate=0.08, files_per_agent_month=0.8,
             agent_monthly_churn=0.08, new_agents_per_month=3, sales_hours_per_new_agent=6,
             cash_cac_per_new_agent=60, delivery_minutes_per_file=75, founder_hours_capacity=60),
    Scenario("base", price_per_file=129, refund_writeoff_rate=0.05, files_per_agent_month=1.0,
             agent_monthly_churn=0.05, new_agents_per_month=5, sales_hours_per_new_agent=4,
             cash_cac_per_new_agent=40, delivery_minutes_per_file=50, founder_hours_capacity=60),
    Scenario("optimistic", price_per_file=149, refund_writeoff_rate=0.03, files_per_agent_month=1.3,
             agent_monthly_churn=0.03, new_agents_per_month=8, sales_hours_per_new_agent=2.5,
             cash_cac_per_new_agent=25, delivery_minutes_per_file=30, founder_hours_capacity=60),
]


def month_economics(s: Scenario, active_agents: float, new_agents: float) -> dict:
    files = active_agents * s.files_per_agent_month
    revenue = files * s.price_per_file
    refunds = revenue * s.refund_writeoff_rate
    variable = files * s.variable_cost_per_file
    acquisition_cash = new_agents * s.cash_cac_per_new_agent
    delivery_hours = files * s.delivery_hours_per_file
    sales_hours = new_agents * s.sales_hours_per_new_agent
    needed_hours = delivery_hours + sales_hours + s.admin_hours_month
    # Delivery beyond the founder's capacity is outsourced; sales and admin stay with the founder.
    founder_delivery_room = max(0.0, s.founder_hours_capacity - sales_hours - s.admin_hours_month)
    outsourced_hours = max(0.0, delivery_hours - founder_delivery_room)
    outsourced_cost = outsourced_hours * s.outsourced_rate_per_hour
    founder_hours = needed_hours - outsourced_hours
    operating_profit = revenue - refunds - variable - s.fixed_monthly - acquisition_cash - outsourced_cost
    return {
        "active_agents": active_agents,
        "new_agents": new_agents,
        "files": files,
        "revenue": revenue,
        "refunds_writeoffs": refunds,
        "variable_costs": variable,
        "fixed_costs": s.fixed_monthly,
        "acquisition_cash": acquisition_cash,
        "outsourced_delivery": outsourced_cost,
        "operating_profit_before_founder_pay": operating_profit,
        "founder_hours": founder_hours,
        "founder_labor_value": founder_hours * s.founder_value_per_hour,
        "profit_after_founder_pay": operating_profit - founder_hours * s.founder_value_per_hour,
    }


def ramp(s: Scenario, months: int = 24) -> list[dict]:
    rows, active = [], 0.0
    for m in range(1, months + 1):
        active = active * (1 - s.agent_monthly_churn) + s.new_agents_per_month
        rows.append({"month": m, **month_economics(s, active, s.new_agents_per_month)})
    return rows


def backsolve(s: Scenario, target: float = TARGET, after_founder_pay: bool = False) -> dict:
    """Smallest steady-state active-agent count whose monthly profit reaches the target.

    Steady state: new agents each month just replace churned ones.
    """
    lo, hi = 0.0, 50_000.0
    key = "profit_after_founder_pay" if after_founder_pay else "operating_profit_before_founder_pay"
    for _ in range(200):
        mid = (lo + hi) / 2
        econ = month_economics(s, mid, mid * s.agent_monthly_churn)
        lo, hi = (lo, mid) if econ[key] >= target else (mid, hi)
    econ = month_economics(s, hi, hi * s.agent_monthly_churn)
    total_hours = econ["files"] * s.delivery_hours_per_file + econ["new_agents"] * s.sales_hours_per_new_agent + s.admin_hours_month
    return {**econ, "total_work_hours": total_hours}


def steady_state_ceiling(s: Scenario) -> float:
    return s.new_agents_per_month / s.agent_monthly_churn


def binom_tail(n: int, p: float, k: int) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def money(x: float) -> str:
    return f"-${-x:,.0f}" if x < 0 else f"${x:,.0f}"


def render() -> str:
    out = []
    w = out.append
    w("# Financial model: Contract-to-Close Desk, plus comparison backsolves\n")
    w("Generated by `python3 model/financial_model.py`. **Don't edit this file by hand.** Change the inputs in the "
      "script instead. These are scenarios to test, not forecasts. Each input is labeled FACT, "
      "ESTIMATE, HYPOTHESIS, or ASSUMPTION in the script.\n")
    w("Definitions: **revenue** is what's invoiced. **Operating profit (before founder pay)** is revenue minus "
      "refunds, write-offs, payment and messaging costs, fixed costs, cash acquisition costs, and any outsourced "
      "delivery labor. That's what you would take home before tax. **Profit after founder pay** also "
      "subtracts your own hours at $40/h, showing whether the business beats a job paying the same "
      "rate.\n")

    w("## 1. Inputs by scenario\n")
    fields = [("Price per file", "price_per_file", money), ("Refunds/write-offs", "refund_writeoff_rate", lambda v: f"{v:.0%}"),
              ("Files per active agent per month", "files_per_agent_month", lambda v: f"{v:.1f}"),
              ("Agent monthly churn", "agent_monthly_churn", lambda v: f"{v:.0%}"),
              ("New paying agents per month", "new_agents_per_month", lambda v: f"{v:g}"),
              ("Sales hours per new agent", "sales_hours_per_new_agent", lambda v: f"{v:g}"),
              ("Cash acquisition cost per new agent", "cash_cac_per_new_agent", money),
              ("Delivery minutes per file", "delivery_minutes_per_file", lambda v: f"{v:g}"),
              ("Founder hours available per month (A3, unconfirmed)", "founder_hours_capacity", lambda v: f"{v:g}")]
    w("| Input | " + " | ".join(s.name for s in SCENARIOS) + " |")
    w("|---|" + "---|" * len(SCENARIOS))
    for label, attr, fmt in fields:
        w(f"| {label} | " + " | ".join(fmt(getattr(s, attr)) for s in SCENARIOS) + " |")
    w(f"| Variable cost per file (cards, invoicing, SMS, email) | " + " | ".join(f"${s.variable_cost_per_file:,.2f}" for s in SCENARIOS) + " |")
    w(f"| **Contribution per file before labor** | " + " | ".join(f"**${s.contribution_per_file:,.2f}**" for s in SCENARIOS) + " |")
    w(f"| Fixed costs per month | " + " | ".join(money(s.fixed_monthly) for s in SCENARIOS) + " |")
    w("")

    w("## 2. 24-month ramp (founder-led sales, no paid ads)\n")
    w("Active agents follow `active = active × (1 − churn) + new`. Delivery hours beyond the founder's capacity are "
      "outsourced at $35/h.\n")
    w("| Scenario | Month | Active agents | Files | Revenue | Operating profit before founder pay | Founder hours | Profit after founder pay @ $40/h |")
    w("|---|---|---|---|---|---|---|---|")
    for s in SCENARIOS:
        rows = ramp(s)
        for m in (3, 6, 12, 24):
            r = rows[m - 1]
            w(f"| {s.name} | {m} | {r['active_agents']:.0f} | {r['files']:.0f} | {money(r['revenue'])} | "
              f"{money(r['operating_profit_before_founder_pay'])} | {r['founder_hours']:.0f} | {money(r['profit_after_founder_pay'])} |")
        hit = next((r["month"] for r in rows if r["operating_profit_before_founder_pay"] >= TARGET), None)
        ceiling = steady_state_ceiling(s)
        w(f"| {s.name} | *$10k month* | *{'month ' + str(hit) if hit else 'not within 24 months'}* | | | "
          f"*ceiling ≈ {ceiling:.0f} agents if acquisition stays at {s.new_agents_per_month:g}/mo* | | |")
    w("")

    w("## 3. Working backward from $10,000/month operating profit\n")
    w("This is the steady state: each month's new agents just replace the ones who churn.\n")
    w("| Scenario | Target basis | Active paying agents | Files/month | Revenue/month | New agents/month to replace churn | Total work hours/month | Founder hours | Outsourced delivery $ |")
    w("|---|---|---|---|---|---|---|---|---|")
    for s in SCENARIOS:
        for after in (False, True):
            b = backsolve(s, after_founder_pay=after)
            over = " ⚠ exceeds capacity" if b["founder_hours"] > s.founder_hours_capacity + 0.5 else ""
            w(f"| {s.name} | {'after paying founder $40/h' if after else 'before founder pay'} | {b['active_agents']:.0f} | "
              f"{b['files']:.0f} | {money(b['revenue'])} | {b['new_agents']:.1f} | {b['total_work_hours']:.0f} | "
              f"{b['founder_hours']:.0f}{over} | {money(b['outsourced_delivery'])} |")
    w("")
    w("⚠ means the sales hours needed just to replace churned agents exceed the founder's assumed capacity. Sales "
      "isn't outsourced in this model, so that row isn't achievable as specified. Conservative economics need a "
      "different channel, not more effort.\n")
    w("**Reading it:** in the base case, $10k/month before founder pay requires about "
      f"{backsolve(SCENARIOS[1])['active_agents']:.0f} agents each sending about one file a month. To hold that level you "
      f"need about {backsolve(SCENARIOS[1])['new_agents']:.1f} new paying agents every month, just to replace churn. "
      "The ramp in section 2 shows founder-led sales at "
      f"{SCENARIOS[1].new_agents_per_month:g} new agents a month plateaus near "
      f"{steady_state_ceiling(SCENARIOS[1]):.0f} agents. So the target needs a channel that scales: brokerage or team "
      "deals, referral loops, or partnerships. A founder working alone, one agent at a time, won't get there. "
      "That's why the experiment measures repeat use and sales hours per agent, not just a first payment.\n")

    w("## 4. Sensitivity: base case, one input changed at a time (month-24 operating profit)\n")
    base = SCENARIOS[1]
    base24 = ramp(base)[-1]["operating_profit_before_founder_pay"]
    tests = [("price $99", replace(base, price_per_file=99)), ("price $179", replace(base, price_per_file=179)),
             ("churn 8%/mo", replace(base, agent_monthly_churn=0.08)), ("churn 3%/mo", replace(base, agent_monthly_churn=0.03)),
             ("3 new agents/mo", replace(base, new_agents_per_month=3)), ("8 new agents/mo", replace(base, new_agents_per_month=8)),
             ("delivery 90 min/file", replace(base, delivery_minutes_per_file=90)), ("delivery 20 min/file", replace(base, delivery_minutes_per_file=20)),
             ("0.7 files/agent/mo", replace(base, files_per_agent_month=0.7))]
    w(f"Base month-24 operating profit: **{money(base24)}**\n")
    w("| Change | Month-24 operating profit | Δ vs base |")
    w("|---|---|---|")
    for label, sc in tests:
        v = ramp(sc)[-1]["operating_profit_before_founder_pay"]
        w(f"| {label} | {money(v)} | {money(v - base24)} |")
    w("\nThe biggest levers are acquisition rate and churn, more than price. That's why the riskiest assumption is about "
      "agents paying *and coming back*, not about the software.\n")

    w("## 5. Experiment arithmetic (why 4 paying agents out of 40)\n")
    w("If each qualified agent independently pays with probability p, the chance of seeing at least 4 payers among "
      "40 contacts is:\n")
    w("| True paid-conversion p | P(≥4 of 40) = CONTINUE signal | P(0 of 40) = STOP signal |")
    w("|---|---|---|")
    for p in (0.02, 0.05, 0.10, 0.15, 0.20, 0.30):
        w(f"| {p:.0%} | {binom_tail(40, p, 4):.0%} | {(1 - p) ** 40:.0%} |")
    w("\nThe rule rarely passes a weak offer (p ≤ 5%) and usually passes a strong one (p ≥ 15%). "
      "Results of 1–3 payers mean ITERATE. Those are your *warmest* contacts. Cold conversion is usually lower, "
      "so if warm conversion is under 5%, reaching ~100 paying agents would take thousands of cold contacts in a single "
      "market.\n")

    w("## 6. Same $10k/month target for the other candidates (backsolve only)\n")
    devex, share = 0.0038, 0.70
    robux = TARGET / (devex * share)
    w("**Roblox game.** Creators \"generally earn 70%\" of Robux sales in their game (FACT, Roblox docs), cashed out "
      f"at the standard $0.0038 DevEx rate: ${devex * share:.5f} per Robux spent. $10k/month needs ≈ **{robux / 1e6:.2f}M Robux spent in "
      "your game every month**. Daily active users needed depend on spend per player (HYPOTHESIS, no public "
      "per-game benchmark):\n")
    w("| Robux spent per DAU per day (hypothesis) | DAU needed |")
    w("|---|---|")
    for rpd in (0.5, 1, 2, 4):
        w(f"| {rpd:g} | {robux / 30 / rpd:,.0f} |")
    w("\nFor reference, the median DevEx payout was **$1,440 a year** (Roblox data, June 2024 to July 2025), and the top 1,000 "
      "creators took most of the pool. Creator Rewards adds engagement-based income on top, but no public rate lets "
      "you model it.\n")
    w("**Trading your own capital.** A bot is only worth what it earns *above* a passive benchmark you could hold "
      "for free. Capital needed for $120k/year of excess return:\n")
    w("| Excess return over benchmark (after costs) | Capital needed |")
    w("|---|---|")
    for alpha in (0.01, 0.03, 0.05, 0.10):
        w(f"| {alpha:.0%} per year | {money(120_000 / alpha)} |")
    w("\nEvidence on retail day traders (97% of persistent Brazilian futures day traders lost money) points to "
      "excess returns at or below zero. Without substantial capital this isn't an income path, even if it works.\n")
    price, churn, platform, aff = 29.0, 0.10, 0.035, 0.30
    net = price * (1 - platform - aff)
    subs = (TARGET + 300) / net
    w(f"**Trading-journal SaaS.** At ${price:.0f}/month with {platform:.1%} payment fees, {aff:.0%} affiliate commission "
      f"(a common channel in trading tools, ESTIMATE) and ~$300/month fixed costs, you need ≈ **{subs:,.0f} paying "
      f"subscribers**. At {churn:.0%} monthly churn (ESTIMATE) that means ≈ {subs * churn:,.0f} new subscribers every month, in a "
      "market where TradeZella, TraderSync, Edgewonk and Tradervue already compete on price.\n")
    fee, win, cac = 250.0, 0.6, 40.0
    clients = (TARGET * 12) / (fee * win - cac)
    w(f"**Property-tax appeals (contingency).** At ${fee:.0f} average fee per successful appeal (Ownwell's own worked "
      f"example is $250; real averages vary by county), a {win:.0%} success rate and ${cac:.0f} to acquire each client "
      f"(HYPOTHESES), $120k/year needs ≈ **{clients:,.0f} signed homeowners a year**, almost all inside a short "
      "seasonal window, in a state where you're allowed to do it.\n")
    return "\n".join(out)


def main() -> None:
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "04-financial-model.md").write_text(render() + "\n", encoding="utf-8")
    outdir = ROOT / "model" / "output"
    outdir.mkdir(parents=True, exist_ok=True)
    for s in SCENARIOS:
        rows = ramp(s)
        with open(outdir / f"ramp_{s.name}.csv", "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            for r in rows:
                writer.writerow({k: round(v, 2) if isinstance(v, float) else v for k, v in r.items()})
    print("wrote docs/04-financial-model.md and model/output/ramp_*.csv")


if __name__ == "__main__":
    main()
