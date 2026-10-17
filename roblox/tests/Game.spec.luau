-- White-box tests for the game rules (the independent, spec-only suite lives in tests/independent/).
local T = require("./TestKit")
local Buyers = require("../src/shared/Buyers")
local Catalog = require("../src/shared/Catalog")
local Crew = require("../src/shared/Crew")
local Economy = require("../src/shared/Economy")
local Houses = require("../src/shared/Houses")
local JobLogic = require("../src/shared/JobLogic")
local Listings = require("../src/shared/Listings")
local Onboarding = require("../src/shared/Onboarding")
local ProfileLogic = require("../src/shared/ProfileLogic")
local SaleFormula = require("../src/shared/SaleFormula")
local ShopRules = require("../src/shared/ShopRules")

local describe, it, expect = T.describe, T.it, T.expect

local function newProfile()
	local p = ProfileLogic.default()
	Economy.ensureStarterKit(p)
	return p
end

describe("SaleFormula worked examples (design spec)", function()
	local rosa = Buyers.get("rosa") :: Buyers.Buyer
	local s = SaleFormula.stagingScore(rosa, { "Cozy", "Cozy", "Bright" }, 3) -- (2+2+1)/6

	it("solo T1 with Love, Love, Like sells for 313", function()
		expect(SaleFormula.price(1, 1, s, 1)).toBe(313)
	end)

	it("two contributors: 328, helper gets 114", function()
		local pay = SaleFormula.payout(1, 1, s, 2)
		expect(pay.price).toBe(328)
		expect(pay.helperPay).toBe(114)
		expect(pay.ownerPay).toBe(328)
	end)

	it("Dream Home: 325 + 25 tip = 350", function()
		local pay = SaleFormula.payout(1, 1, 1, 1)
		expect(pay.price).toBe(325)
		expect(pay.tip).toBe(25)
		expect(pay.total).toBe(350)
		expect(SaleFormula.reaction(1, 1)).toBe("dream")
	end)

	it("worst case C=0.5, S=-0.5 sells for 149", function()
		expect(SaleFormula.price(1, 0.5, -0.5, 1)).toBe(149)
	end)
end)

describe("SaleFormula invariants", function()
	it("no flip loses coins over the whole grid", function()
		for tier = 1, 3 do
			local b = Houses.get(tier).price
			for ci = 0, 10 do
				local c = 0.5 + ci * 0.05
				for si = 0, 15 do
					local s = -0.5 + si * 0.1
					for n = 1, 4 do
						expect(SaleFormula.price(tier, c, s, n) > b).toBeTruthy()
					end
				end
			end
		end
	end)

	it("caps the crew multiplier at 1.15 and S at [-0.5, 1]", function()
		expect(SaleFormula.crewMultiplier(9)).toBeNear(1.15)
		local dislikes = Buyers.get("rosa") :: Buyers.Buyer
		expect(SaleFormula.stagingScore(dislikes, { "Modern", "Modern", "Modern" }, 3)).toBeNear(-0.5)
	end)

	it("breakdown lines add up to the price within rounding", function()
		local b = SaleFormula.breakdown(2, 0.8, 0.5, 3)
		expect(math.abs(b.base + b.repairs + b.staging + b.crew - b.price)).toBeAtMost(2)
		expect(b.floorApplied).toBeFalsy()
	end)

	it("daily bonus adds 25% once", function()
		expect(SaleFormula.withDailyBonus(313, true)).toBe(391)
		expect(SaleFormula.withDailyBonus(313, false)).toBe(313)
	end)
end)

describe("JobLogic", function()
	it("work only moves forward and tool power never overshoots", function()
		local spot = JobLogic.newSpot("junk_1", "junk", 4)
		expect(select(1, JobLogic.applyHit(spot, 1, 3))).toBeTruthy()
		local accepted, done = JobLogic.applyHit(spot, 1, 3)
		expect(accepted).toBeTruthy()
		expect(done).toBeTruthy()
		expect(spot.done).toBe(4)
		expect(select(1, JobLogic.applyHit(spot, 1, 1))).toBeFalsy()
	end)

	it("pipe ignores tool power", function()
		local pipe = JobLogic.newSpot("pipe_1", "pipe", 3)
		JobLogic.applyHit(pipe, 1, 3)
		expect(pipe.done).toBe(1)
	end)

	it("needle is a 1.2 s triangle wave", function()
		expect(JobLogic.needlePosition(10, 10)).toBeNear(0)
		expect(JobLogic.needlePosition(10.3, 10)).toBeNear(0.5)
		expect(JobLogic.needlePosition(10.6, 10)).toBeNear(1)
		expect(JobLogic.needlePosition(10.9, 10)).toBeNear(0.5)
		expect(JobLogic.needlePosition(11.2, 10)).toBeNear(0)
	end)

	it("judges presses with 150 ms of latency tolerance", function()
		local w = 0.25 -- zone [0.375, 0.625] => needle inside for t in [0.225, 0.375] on the way up
		expect(JobLogic.judgePipe(0.30, 0, w)).toBeTruthy()
		expect(JobLogic.judgePipe(0.50, 0, w)).toBeTruthy() -- 0.50-0.15 = 0.35 still inside
		expect(JobLogic.judgePipe(0.54, 0, w)).toBeFalsy() -- window [0.39, 0.54] is all above the zone
		expect(JobLogic.judgePipe(0.10, 0, w)).toBeFalsy()
	end)

	it("judges correctly across the peak", function()
		-- Zone 0.9 wide covers [0.05, 0.95]; around the peak (t=0.6) the needle exceeds 0.95,
		-- but the window [0.45, 0.6] starts at 0.75, inside the zone.
		expect(JobLogic.judgePipe(0.6, 0, 0.9)).toBeTruthy()
	end)

	it("zone widens per miss, doubles with Hold it, and caps at 0.9", function()
		expect(JobLogic.pipeZoneWidth(0, false, false)).toBeNear(0.25)
		expect(JobLogic.pipeZoneWidth(0, true, false)).toBeNear(0.40)
		expect(JobLogic.pipeZoneWidth(2, false, false)).toBeNear(0.45)
		expect(JobLogic.pipeZoneWidth(1, false, true)).toBeNear(0.70)
		expect(JobLogic.pipeZoneWidth(9, true, true)).toBeNear(0.9)
	end)

	it("couch needs two different lifters within 5 s", function()
		local couch = JobLogic.newCouch()
		expect(JobLogic.liftCouch(couch, 1, "left", 0)).toBeFalsy()
		expect(JobLogic.liftCouch(couch, 1, "right", 1)).toBeFalsy()
		expect(JobLogic.liftCouch(couch, 2, "left", 7)).toBeFalsy() -- right was lifted at 1, too long ago
		expect(JobLogic.liftCouch(couch, 1, "right", 8)).toBeTruthy()
	end)

	it("raccoon leaves after 3 shoos, or 1 with a pincer", function()
		local r = JobLogic.newSpot("raccoon_1", "raccoon", 3)
		expect(JobLogic.shooRaccoon(r, 1, false)).toBeFalsy()
		expect(JobLogic.shooRaccoon(r, 1, false)).toBeFalsy()
		expect(JobLogic.shooRaccoon(r, 1, false)).toBeTruthy()
		local r2 = JobLogic.newSpot("raccoon_1", "raccoon", 3)
		expect(JobLogic.shooRaccoon(r2, 1, true)).toBeTruthy()
	end)
end)

describe("Economy and the onboarding path (A17)", function()
	it("first Shack free, first sale 313, decor 150, second Shack 100", function()
		local p = newProfile()
		local ok, _, paid = Economy.buyListing(p, 1)
		expect(ok).toBeTruthy()
		expect(paid).toBe(0)
		local rosa = Buyers.get("rosa") :: Buyers.Buyer
		local s = SaleFormula.stagingScore(rosa, { "Cozy", "Cozy", "Bright" }, 3) -- starter kit pieces
		local pay = SaleFormula.payout(1, 1, s, 1)
		-- The first flip of a day gets +25%; the design's 313 path is the no-bonus case.
		p.lastBonusDay = 100
		local credited = Economy.creditSale(p, pay.ownerPay, 100)
		Economy.recordFlip(p, 1, pay.price, "rosa", false)
		expect(credited).toBe(313)
		expect(select(1, Economy.buyItem(p, "cozy_plant"))).toBeTruthy()
		expect(p.coins).toBe(163)
		local ok2, _, paid2 = Economy.buyListing(p, 1)
		expect(ok2).toBeTruthy()
		expect(paid2).toBe(100)
		expect(p.coins).toBe(63)
	end)

	it("with the daily bonus the first sale pays 391", function()
		local p = newProfile()
		expect(select(1, Economy.creditSale(p, 313, 5))).toBe(391)
		expect(select(1, Economy.creditSale(p, 313, 5))).toBe(313)
		expect(select(1, Economy.creditSale(p, 313, 6))).toBe(391)
	end)

	it("failed purchases leave the profile unchanged", function()
		local p = newProfile()
		p.coins = 50
		p.claimedFreeShack = true
		p.flipsCompleted = 1
		p.ownedDecor.cozy_art = true
		local before = p.coins
		expect(select(2, Economy.buyItem(p, "cozy_plant"))).toBe("not_enough_coins")
		expect(select(2, Economy.buyItem(p, "cozy_art"))).toBe("already_owned")
		expect(select(2, Economy.buyItem(p, "cozy_rug"))).toBe("not_for_coins") -- starter kit, never sold
		expect(select(2, Economy.buyItem(p, "tool_pro"))).toBe("tier_locked")
		expect(select(2, Economy.buyItem(p, "pass_crew_hats"))).toBe("not_for_coins")
		expect(select(2, Economy.buyListing(p, 2))).toBe("tier_locked")
		expect(p.coins).toBe(before)
	end)

	it("rescues a broke player with a free Starter Shack (A13a)", function()
		local p = newProfile()
		p.flipsCompleted = 4
		p.claimedFreeShack = true
		p.coins = 40
		local ok, _, paid = Economy.buyListing(p, 1)
		expect(ok).toBeTruthy()
		expect(paid).toBe(0)
		p.coins = 100
		local _, _, paid2 = Economy.buyListing(p, 1)
		expect(paid2).toBe(100)
	end)

	it("recordFlip unlocks tiers at 3 and 8 flips and keeps best prices", function()
		local p = newProfile()
		for _ = 1, 3 do
			Economy.recordFlip(p, 1, 300, "max", false)
		end
		expect(p.unlockedTier).toBe(2)
		Economy.recordFlip(p, 1, 250, "max", true)
		expect(p.bestPriceByTier["1"]).toBe(300)
		expect(p.buyerBook.max.dream).toBeTruthy()
		for _ = 1, 4 do
			Economy.recordFlip(p, 2, 700, "ivy", false)
		end
		expect(p.unlockedTier).toBe(3)
	end)
end)

describe("Catalog", function()
	it("passes the kid-safe shop rules with every Robux slot covered by coins", function()
		expect(#ShopRules.validateCatalog(Catalog.SHOP)).toBe(0)
		expect(#ShopRules.slotsWithoutEarnedOption(Catalog.SHOP)).toBe(0)
		for _, item in Catalog.SHOP do
			expect(item.kind ~= "devproduct").toBeTruthy()
			if item.kind == "gamepass" then
				expect(item.passId).toBe(0)
			end
		end
	end)

	it("has 20 decor pieces and a 5-piece starter kit", function()
		expect(#Catalog.DECOR).toBe(20)
		for _, id in Catalog.STARTER_DECOR do
			expect(Catalog.decor(id) ~= nil).toBeTruthy()
		end
	end)
end)

describe("Listings, Onboarding and Crew", function()
	it("lists two houses per unlocked tier, Rosa first when the Shack is free", function()
		local n = 0
		local list = Listings.generate(2, function(lo, hi)
			n += 1
			return lo + (n % (hi - lo + 1))
		end, true)
		expect(#list).toBe(4)
		expect(list[1].buyerId).toBe("rosa")
		expect(list[1].free).toBeTruthy()
		expect(list[1].price).toBe(0)
		expect(list[2].free).toBeFalsy()
		expect(list[3].price).toBe(240)
		expect(list[3].buyerId ~= list[4].buyerId).toBeTruthy()
	end)

	it("onboarding only moves forward", function()
		local cur, steps = Onboarding.advance(2, 5)
		expect(cur).toBe(5)
		expect(steps).toEqual({ 3, 4, 5 })
		local cur2, steps2 = Onboarding.advance(5, 4)
		expect(cur2).toBe(5)
		expect(#steps2).toBe(0)
		expect(Onboarding.stepName(11)).toBe("SecondHouseBought")
	end)

	it("crew joining respects size and mode", function()
		local crew = Crew.new(1, "Open")
		for id = 2, 4 do
			expect(select(1, Crew.canJoin(crew, id, false))).toBeTruthy()
			Crew.join(crew, id)
		end
		expect(select(2, Crew.canJoin(crew, 5, true))).toBe("crew_full")
		local friends = Crew.new(1, "Friends")
		expect(select(2, Crew.canJoin(friends, 2, false))).toBe("friends_only")
		expect(select(1, Crew.canJoin(friends, 2, true))).toBeTruthy()
	end)

	it("counts contributors and lists helpers", function()
		local crew = Crew.new(1, "Open")
		Crew.join(crew, 2)
		expect(Crew.contributorCount(crew)).toBe(1)
		Crew.markContributor(crew, 2)
		Crew.markContributor(crew, 99) -- not a member: ignored
		expect(Crew.contributorCount(crew)).toBe(1)
		expect(Crew.helpers(crew)).toEqual({ 2 })
		Crew.markContributor(crew, 1)
		expect(Crew.contributorCount(crew)).toBe(2)
		Crew.leave(crew, 2)
		expect(Crew.contributorCount(crew)).toBe(1)
	end)
end)

describe("Profile migration (A16)", function()
	it("reconciles the new fields from damaged data", function()
		local p = ProfileLogic.reconcile({
			ownedDecor = { cozy_rug = true, x = 1 },
			ownedTools = { pro = true },
			buyerBook = { rosa = { sold = true }, bad = 5 },
			bestPriceByTier = { ["1"] = 313.7, [2] = 9 },
			lastBonusDay = -3,
			claimedFreeShack = "yes",
		})
		expect(p.ownedDecor).toEqual({ cozy_rug = true })
		expect(p.ownedTools).toEqual({ pro = true })
		expect(p.buyerBook).toEqual({ rosa = { sold = true, dream = false } })
		expect(p.bestPriceByTier).toEqual({ ["1"] = 313 })
		expect(p.lastBonusDay).toBe(0)
		expect(p.claimedFreeShack).toBeFalsy()
	end)
end)

return nil
