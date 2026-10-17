# Fixer-Upper Friends: acceptance criteria (graybox MVP)

Written 2026-10-17, **before** any gameplay code. Source: `docs/design-spec.json` (judged
synthesis of three independent designs) and `docs/research-facts.json` (105 facts from official
Roblox docs, filings, and APIs). Changes after this point must be recorded here with a reason.

## What can and can't be verified in this environment

Verifiable here (Linux, no Roblox Studio):
- **Pure game logic** under Lune 0.11, using the same `require("./X")` semantics as Roblox.
- **Place file build** with Rojo 7.7.1.
- **Linting** with Selene 0.31 against the full Roblox API, and **formatting** with StyLua 2.6.

**Not verifiable here:** anything that needs the Roblox engine. That covers physics, ProximityPrompt
behavior, GUI rendering, data stores, AnalyticsService delivery, and real players. Those items are
listed under "Studio checklist" and stay **unverified** until someone runs them in Studio.

## A. Rules (pure logic, Lune-tested)

| ID | Criterion |
|----|-----------|
| A1 | Tier table: T1 V=250 B=100 Work=25 pads=3 unlock 0 flips; T2 V=600 B=240 Work=52 pads=4 unlock 3; T3 V=1400 B=560 Work=79 pads=5 unlock 8. Work totals are computed from the spot list, not typed in. |
| A2 | Sale price `P = max(B + round(0.1V), round(V(0.4+0.6C)(1+0.3S)(1+0.05(n−1))))`. Tip `round(0.1V)` only when C=1 and S=1. The 4 worked examples hold exactly: 313; 328 with helper pay 114; 350 Dream Home; 149 worst case. |
| A3 | **No flip loses coins:** for every tier, C∈[0.5,1], S∈[−0.5,1], n∈1..4, P > B. Checked over a grid. |
| A4 | S = clamp(Σtaste/(2K), −0.5, 1) with Love +2, Like +1, Neutral 0, Dislike −1, and empty pads 0. Paint color and hats are **not** inputs to P. |
| A5 | Crew multiplier is capped at 1.15. Crew Pay = round(0.5·(Total − B)) to each non-owner contributor. A non-contributor gets 0. |
| A6 | First flip of a UTC day adds +25% to that player's own payout, at most once per day. No streak state exists. |
| A7 | Job work only moves forward and never exceeds the spot's Work. Tool power multiplies hits, but the pipe always needs 3 successes. |
| A8 | Pipe timing judge: the needle is a triangle wave on a 1.2 s cycle, and the green zone is centered. Zone width starts at 25% (40% in onboarding), grows +10 points per miss to a cap, and doubles with "Hold it". The press is judged against the needle anywhere in [arrival − 150 ms, arrival]. |
| A9 | Two-hand couch: both lifts by **different** crew members within 5 s complete it; the solo drag also completes it. Raccoon: 3 shoos, or 1 with a valid pincer. |
| A10 | Rate caps: bonk ≤ 1 per 0.25 s per player; any action over its cap is rejected without side effects. |
| A11 | Buyer pool of 8 with Love, Like, and Dislike styles (all distinct). Rosa = Loves Cozy, Likes Bright, Dislikes Modern. Reaction tiers: S≤0 head-scratch; 0<S<0.5 nod; S≥0.5 jump; C=1 and S=1 Dream Home. |
| A12 | Listings: 2 per unlocked tier, and the buyer is drawn by an injected RNG from the pool. The first Starter Shack is free exactly once. |
| A13 | Economy: buying a listing needs coins ≥ B and the tier unlocked. Shop purchases need coins ≥ price, an item not already owned, and tool tier prerequisites. Each failure returns a reason and leaves the profile unchanged. |
| A14 | Onboarding: steps 1–11 frozen (names and numbers fixed); progress only moves forward; each step is reported at most once. |
| A15 | Catalog passes `ShopRules.validateCatalog`, and `slotsWithoutEarnedOption` is empty. There are **zero** developer products and no coin grants for Robux. All game-pass ids are 0 in the MVP. |
| A16 | Profile reconcile handles the new fields (ownedDecor, ownedTools, buyerBook, bestPriceByTier, lastBonusDay) from nil, damaged, or old data. |
| A13a | *Amendment 2026-10-17, written before the economy code:* **soft-lock rescue.** The spec's "free Starter Shack exactly once" can trap a player. If they claim the free Shack and leave before selling, or spend coins below the 100-coin Shack price with no house, they can never earn again. Rule: a T1 listing is also free whenever the player's coins are below the T1 price. This can't be farmed for profit beyond normal play, because coins are never sold and a free Shack pays the same as any T1 flip. |
| A17 | Pace check (simulated): with the design's timings, one solo T1 flip affords one 150-coin decor piece and then the 100-coin second Shack (the step 10→11 path stays reachable). |

## B. Engine integration (static checks here; behavior in Studio)

| ID | Criterion | Checked here by |
|----|-----------|-----------------|
| B1 | `rojo build` produces a place file with Script, LocalScript, and ModuleScripts in the right services | build plus a structural check of the .rbxlx |
| B2 | Selene reports 0 errors against the generated Roblox std; StyLua reports no diffs | selene / stylua --check |
| B3 | Clients send only ids or enums; the server never reads a price, amount, outcome, or position from a client. Every remote handler type-checks its args and rate-limits. | code review workflow + grep test |
| B4 | Every ProximityPrompt sets HoldDuration, MaxActivationDistance, and RequiresLineOfSight explicitly | Lune test over the prompt spec table |
| B5 | Server re-checks distance (≤ 12 studs), crew membership, and spot state on every prompt trigger | review |
| B6 | Economy events are logged only after a successful save, never with amount 0, and never from the client | review + grep test |
| B7 | No free-text input, no custom chat, no Seats or beds/toilets/tubs, no external links, no audio or asset ids | grep test over src |
| B8 | No Robux prices are hard-coded in UI strings | grep test |

## C. Studio checklist (unverified until run in Roblox Studio)

1. Open `build/FixerUpperFriends.rbxlx`, press Play: spawn at your lot with an arrow to the Listing Board.
2. Complete the 11 onboarding steps solo in ≤ 5 min. Output shows `[Analytics] onboarding:1..11`.
3. Two-player local server test (Test → Clients and Servers, 2 players): a helper joins a lot, works, and gets Crew Pay; the owner alone can sell.
4. Leave and rejoin with Studio API access on a **separate test universe**: coins, decor, tools, and flips persist.
5. MicroProfiler: no server script > 2 ms/frame during a 4-player flip; part count per house ≤ 60.
6. Mobile emulator: every job is completable by touch.

## D. Playtest thresholds

Pre-registered in [playtest-thresholds.json](playtest-thresholds.json). They're judgment calls
anchored on GameAnalytics 2025 (secondary) and official Roblox guidance, as each entry states.
They require real players and elapsed time: **nothing has been measured yet.**
