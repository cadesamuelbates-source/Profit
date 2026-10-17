local T = require("./TestKit")
local ProfileLogic = require("../src/shared/ProfileLogic")
local RateLimiter = require("../src/shared/RateLimiter")

local describe, it, expect = T.describe, T.it, T.expect

describe("ProfileLogic.reconcile", function()
	it("builds defaults from nil", function()
		local p = ProfileLogic.reconcile(nil)
		expect(p.coins).toBe(0)
		expect(p.unlockedTier).toBe(1)
		expect(p.version).toBe(ProfileLogic.VERSION)
	end)

	it("repairs damaged values instead of trusting them", function()
		local p = ProfileLogic.reconcile({
			coins = -50,
			xp = 0 / 0,
			flipsCompleted = math.huge,
			unlockedTier = 0,
			ownedCosmetics = { paint_teal = true, bad = "yes", [5] = true },
			joinDays = { 20000, "x" },
			purchaseLedger = { "abc", 7 },
			hacked = true,
		})
		expect(p.coins).toBe(0)
		expect(p.xp).toBe(0)
		expect(p.flipsCompleted).toBe(0)
		expect(p.unlockedTier).toBe(1)
		expect(p.ownedCosmetics).toEqual({ paint_teal = true })
		expect(p.joinDays).toEqual({ 20000 })
		expect(p.purchaseLedger).toEqual({ "abc" })
		expect((p :: any).hacked).toBe(nil)
	end)

	it("floors fractional currency", function()
		expect(ProfileLogic.reconcile({ coins = 10.9 }).coins).toBe(10)
	end)
end)

describe("ProfileLogic session locking", function()
	it("acquires an unlocked key", function()
		local value, meta = ProfileLogic.acquire(nil, nil, "server-A", 1000)
		expect(value ~= nil).toBeTruthy()
		expect(meta).toEqual({ lockId = "server-A", lockedAt = 1000 })
	end)

	it("refuses a fresh lock held by another server", function()
		local value = ProfileLogic.acquire({ coins = 5 }, { lockId = "server-B", lockedAt = 1000 }, "server-A", 1100)
		expect(value).toBe(nil)
	end)

	it("takes over a stale lock after the expiry", function()
		local later = 1000 + ProfileLogic.LOCK_EXPIRY_SECONDS + 1
		local value, meta = ProfileLogic.acquire({ coins = 5 }, { lockId = "server-B", lockedAt = 1000 }, "server-A", later)
		expect(value and value.coins).toBe(5)
		expect(meta and meta.lockId).toBe("server-A")
	end)

	it("re-acquires its own lock", function()
		local value = ProfileLogic.acquire({ coins = 1 }, { lockId = "server-A", lockedAt = 1 }, "server-A", 2)
		expect(value ~= nil).toBeTruthy()
	end)

	it("cancels a save when the lock was lost", function()
		local p = ProfileLogic.default()
		local value = ProfileLogic.save(p, { lockId = "server-B", lockedAt = 5 }, "server-A", 10, false)
		expect(value).toBe(nil)
		expect(ProfileLogic.save(p, nil, "server-A", 10, false)).toBe(nil)
	end)

	it("refreshes the lock on save and clears it on release", function()
		local p = ProfileLogic.default()
		local _, meta = ProfileLogic.save(p, { lockId = "server-A", lockedAt = 5 }, "server-A", 10, false)
		expect(meta).toEqual({ lockId = "server-A", lockedAt = 10 })
		local _, released = ProfileLogic.save(p, { lockId = "server-A", lockedAt = 5 }, "server-A", 10, true)
		expect(released).toEqual({})
	end)
end)

describe("ProfileLogic receipt ledger", function()
	it("records each purchase once", function()
		local p = ProfileLogic.default()
		ProfileLogic.recordPurchase(p, "p1")
		ProfileLogic.recordPurchase(p, "p1")
		expect(#p.purchaseLedger).toBe(1)
		expect(ProfileLogic.hasPurchase(p, "p1")).toBeTruthy()
		expect(ProfileLogic.hasPurchase(p, "p2")).toBeFalsy()
	end)

	it("keeps only the most recent ids", function()
		local p = ProfileLogic.default()
		for i = 1, ProfileLogic.LEDGER_LIMIT + 5 do
			ProfileLogic.recordPurchase(p, "p" .. i)
		end
		expect(#p.purchaseLedger).toBe(ProfileLogic.LEDGER_LIMIT)
		expect(ProfileLogic.hasPurchase(p, "p1")).toBeFalsy()
		expect(ProfileLogic.hasPurchase(p, "p" .. (ProfileLogic.LEDGER_LIMIT + 5))).toBeTruthy()
	end)
end)

describe("ProfileLogic retention", function()
	local DAY = 86400
	it("counts days since first join and fires once per day", function()
		local p = ProfileLogic.default()
		local d0 = 20000 * DAY + 3600
		local since, first = ProfileLogic.recordJoin(p, d0)
		expect(since).toBe(0)
		expect(first).toBeTruthy()
		local _, againToday = ProfileLogic.recordJoin(p, d0 + 7200)
		expect(againToday).toBeFalsy()
		local sinceD1 = ProfileLogic.recordJoin(p, d0 + DAY)
		expect(sinceD1).toBe(1)
		ProfileLogic.recordJoin(p, d0 + 7 * DAY)
		expect(ProfileLogic.returnedOnDay(p, 1)).toBeTruthy()
		expect(ProfileLogic.returnedOnDay(p, 7)).toBeTruthy()
		expect(ProfileLogic.returnedOnDay(p, 2)).toBeFalsy()
	end)

	it("uses UTC day boundaries", function()
		expect(ProfileLogic.dayIndex(DAY - 1)).toBe(0)
		expect(ProfileLogic.dayIndex(DAY)).toBe(1)
	end)

	it("caps stored join days", function()
		local p = ProfileLogic.default()
		for d = 0, ProfileLogic.JOIN_DAYS_LIMIT + 9 do
			ProfileLogic.recordJoin(p, d * DAY)
		end
		expect(#p.joinDays).toBe(ProfileLogic.JOIN_DAYS_LIMIT)
		expect(p.firstJoinDay).toBe(0)
	end)
end)

describe("RateLimiter", function()
	it("allows a burst up to capacity, then refills over time", function()
		local rl = RateLimiter.new(3, 1)
		expect(rl:allow("u1:job", 0)).toBeTruthy()
		expect(rl:allow("u1:job", 0)).toBeTruthy()
		expect(rl:allow("u1:job", 0)).toBeTruthy()
		expect(rl:allow("u1:job", 0)).toBeFalsy()
		expect(rl:allow("u1:job", 1)).toBeTruthy()
		expect(rl:allow("u2:job", 0)).toBeTruthy()
	end)

	it("forgets a player's buckets", function()
		local rl = RateLimiter.new(1, 0)
		rl:allow("u1:a", 0)
		rl:forget("u1:")
		expect(rl:allow("u1:a", 0)).toBeTruthy()
	end)
end)

return nil
