# Pure module API contract (src/shared)

Fixed before implementation so tests can be written independently. All modules are pure Luau,
with no Roblox globals. They are required as `require("../src/shared/<Name>")` from `tests/`.
Numbers use `round(x) = math.floor(x + 0.5)`.

## Houses
- `Houses.TIERS: { [number]: TierDef }` for tiers 1..3, where
  `TierDef = { tier, name, value, price, unlockFlips, pads, spots: { { kind, count, work } } }`.
  Kinds: `"junk"(work 4)`, `"pipe"(3)`, `"patch"(3)`, `"window"(2)`, `"paint"(3)`, `"couch"(3)`, `"raccoon"(3)`, `"porch"(3)`.
- `Houses.get(tier) -> TierDef` (errors on an unknown tier)
- `Houses.totalWork(tier) -> number` (sum of count × work)
- `Houses.spotList(tier) -> { { id: string, kind: string, work: number } }` with ids `kind_index` (e.g. `"junk_1"`), in spot-list order
- `Houses.unlockedTier(flipsCompleted) -> number` (highest tier whose unlockFlips ≤ flips)

## Buyers
- `Buyers.STYLES = { "Cozy", "Modern", "Rustic", "Bright" }`
- `Buyers.POOL`: 8 entries `{ id, name, love, like, dislike }` (three distinct styles each)
- `Buyers.get(id) -> Buyer?`
- `Buyers.taste(buyer, style?) -> number`: +2 love, +1 like, −1 dislike, 0 otherwise or nil

## SaleFormula
- `SaleFormula.round(x)`
- `SaleFormula.stagingScore(buyer, padStyles: { string? }, padCount) -> S`. `padStyles[i]` is the style on pad i, or nil if empty. `S = clamp(Σ taste / (2·padCount), −0.5, 1)`
- `SaleFormula.crewMultiplier(n) -> number` (`1 + 0.05·(n−1)`, n clamped to 1..4)
- `SaleFormula.price(tier, C, S, n) -> number`: `max(B + round(0.1V), round(V(0.4+0.6C)(1+0.3S)·crewMultiplier(n)))`
- `SaleFormula.tip(tier, C, S) -> number`: `round(0.1V)` iff C == 1 and S == 1, else 0
- `SaleFormula.payout(tier, C, S, n) -> { price, tip, total, ownerPay, helperPay }`. `ownerPay = total`; `helperPay = round(0.5·(total − B))` for each non-owner contributor (0 if n == 1)
- `SaleFormula.withDailyBonus(amount, eligible: boolean) -> number` (`round(amount × 1.25)` when eligible)
- `SaleFormula.reaction(C, S) -> "dream" | "jump" | "nod" | "scratch"`
- `SaleFormula.breakdown(tier, C, S, n) -> { base, repairs, staging, crew, floorApplied: boolean, price, tip, total }`. The lines are rounded components of the formula; `price` is authoritative

## JobLogic
- `JobLogic.newSpot(id, kind, work) -> Spot` (`{ id, kind, work, done = 0, hitters = {} }`)
- `JobLogic.applyHit(spot, userId, power) -> (accepted: boolean, completedNow: boolean)`. Adds `power`, clamped to `work`. A complete spot rejects further hits. The pipe ignores power (+1 per success)
- `JobLogic.condition(spots) -> C` (Σdone / Σwork, 0 for no spots)
- `JobLogic.MIN_INTERVAL: { [kind]: seconds }`, where `junk = 0.25`
- `JobLogic.needlePosition(t, sweepStart) -> number in [0,1]` (triangle wave, period 1.2 s: 0 → 1 at 0.6 s → 0 at 1.2 s)
- `JobLogic.pipeZoneWidth(misses, onboarding, holdIt) -> number`: base 0.25 (0.40 onboarding), +0.10 per miss, ×2 with holdIt, capped at 0.9
- `JobLogic.judgePipe(arrival, sweepStart, zoneWidth) -> boolean`: true if the needle is inside `[0.5 − w/2, 0.5 + w/2]` at any time in `[arrival − 0.15, arrival]`
- `JobLogic.newCouch() -> Couch`. `JobLogic.liftCouch(couch, userId, side: "left"|"right", now) -> completed: boolean` completes when the two sides are lifted by different users within 5 s
- `JobLogic.shooRaccoon(spot, userId, pincer: boolean) -> completedNow` (3 shoos, or 1 with pincer)

## Catalog
- `Catalog.DECOR`: 20 entries `{ id, name, style, shape }`, 4 styles × 5 shapes (`"Rug","Lamp","Plant","Chair","Art"`); ids are `lower(style).."_"..lower(shape)`
- `Catalog.STARTER_DECOR`: `{ "cozy_rug", "cozy_lamp", "bright_plant", "modern_chair", "rustic_chair" }`
- `Catalog.DECOR_PRICE = 150`
- `Catalog.TOOLS = { basic = { power = 1, price = 0, requiresTier = 1 }, pro = { power = 2, price = 600, requiresTier = 2 }, master = { power = 3, price = 2000, requiresTier = 3 } }`
- `Catalog.toolPower(ownedTools: { [string]: boolean }) -> number`
- `Catalog.SHOP: { ShopRules.Item }`, the full shop including 3 game passes (ids 0) and earned items; must pass `ShopRules`

## Economy (mutates a ProfileLogic profile)
- `Economy.buyListing(profile, tier) -> (ok, reason?)`. Starter Shack (tier 1) is free if `profile.flipsCompleted == 0 and not profile.claimedFreeShack`
- `Economy.buyItem(profile, itemId) -> (ok, reason?, price?)` for decor and tools
- `Economy.creditSale(profile, amount, utcDay) -> (credited, bonusApplied)` applies the first-flip-of-day bonus
- `Economy.recordFlip(profile, tier, price, buyerId, dream)` updates flips, unlockedTier, bestPriceByTier, buyerBook

## Onboarding
- `Onboarding.STEPS`: 11 entries `{ step, name }`: Joined, ArrivedAtLot, ClaimedStarterShack, FirstHit, FirstSpotDone, FirstPipeFixed, HouseRepaired, FirstDecorStaged, FirstSale, FirstShopPurchase, SecondHouseBought
- `Onboarding.advance(current, reached) -> (newCurrent, stepsToLog: { number })`, forward only; logs current+1..reached

## Listings
- `Listings.generate(unlockedTier, randomInt: (lo, hi) -> number, freeStarter: boolean) -> { { tier, buyerId, price, free } }`: 2 per unlocked tier; with `freeStarter`, the first T1 listing is free with price 0

## Crew
- `Crew.new(ownerId, mode: "Open"|"Friends"|"Solo") -> Crew`
- `Crew.canJoin(crew, userId, isFriend) -> (ok, reason?)` (max 4 members including the owner)
- `Crew.join(crew, userId)`, `Crew.leave(crew, userId)`
- `Crew.markContributor(crew, userId)`, `Crew.contributorCount(crew) -> n` (≥ 1), `Crew.helpers(crew) -> { userId }` (contributors other than the owner)
