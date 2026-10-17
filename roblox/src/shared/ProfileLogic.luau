--!strict
-- Pure player-profile logic: defaults, migration, session locking, the receipt
-- ledger and retention-day bookkeeping. No Roblox APIs, so it runs in Lune tests.
--
-- Session locking follows Roblox's player-data guidance: the lock lives in the
-- key's metadata and is checked/written inside the same UpdateAsync transform.

local ProfileLogic = {}

ProfileLogic.VERSION = 1
ProfileLogic.LOCK_EXPIRY_SECONDS = 30 * 60 -- a crashed server's lock is ignored after this
ProfileLogic.LEDGER_LIMIT = 100 -- most recent purchase ids kept for duplicate detection
ProfileLogic.JOIN_DAYS_LIMIT = 60

export type Profile = {
	version: number,
	coins: number,
	xp: number,
	flipsCompleted: number,
	unlockedTier: number,
	ownedCosmetics: { [string]: boolean },
	equipped: { [string]: string },
	onboardingStep: number,
	firstJoinDay: number?,
	joinDays: { number },
	purchaseLedger: { string },
}

export type Meta = { lockId: string?, lockedAt: number? }

function ProfileLogic.default(): Profile
	return {
		version = ProfileLogic.VERSION,
		coins = 0,
		xp = 0,
		flipsCompleted = 0,
		unlockedTier = 1,
		ownedCosmetics = {},
		equipped = {},
		onboardingStep = 0,
		firstJoinDay = nil,
		joinDays = {},
		purchaseLedger = {},
	}
end

local function nonNegativeInteger(value: any, fallback: number): number
	if type(value) ~= "number" or value ~= value or value < 0 or value == math.huge then
		return fallback
	end
	return math.floor(value)
end

-- Accepts whatever came out of the data store (possibly nil, old, or damaged) and
-- returns a well-formed profile. Unknown fields are dropped.
function ProfileLogic.reconcile(raw: any): Profile
	local profile = ProfileLogic.default()
	if type(raw) ~= "table" then
		return profile
	end
	profile.coins = nonNegativeInteger(raw.coins, 0)
	profile.xp = nonNegativeInteger(raw.xp, 0)
	profile.flipsCompleted = nonNegativeInteger(raw.flipsCompleted, 0)
	profile.unlockedTier = math.max(1, nonNegativeInteger(raw.unlockedTier, 1))
	profile.onboardingStep = nonNegativeInteger(raw.onboardingStep, 0)
	if type(raw.firstJoinDay) == "number" then
		profile.firstJoinDay = nonNegativeInteger(raw.firstJoinDay, 0)
	end
	if type(raw.ownedCosmetics) == "table" then
		for id, owned in raw.ownedCosmetics do
			if type(id) == "string" and owned == true then
				profile.ownedCosmetics[id] = true
			end
		end
	end
	if type(raw.equipped) == "table" then
		for slot, id in raw.equipped do
			if type(slot) == "string" and type(id) == "string" then
				profile.equipped[slot] = id
			end
		end
	end
	if type(raw.joinDays) == "table" then
		for _, day in raw.joinDays do
			if type(day) == "number" then
				table.insert(profile.joinDays, nonNegativeInteger(day, 0))
			end
		end
	end
	if type(raw.purchaseLedger) == "table" then
		for _, purchaseId in raw.purchaseLedger do
			if type(purchaseId) == "string" then
				table.insert(profile.purchaseLedger, purchaseId)
			end
		end
	end
	return profile
end

-- Lock decisions -------------------------------------------------------------

function ProfileLogic.isLockedByOther(meta: Meta?, lockId: string, now: number): boolean
	if not meta or meta.lockId == nil or meta.lockId == lockId then
		return false
	end
	local lockedAt = meta.lockedAt or 0
	return now - lockedAt < ProfileLogic.LOCK_EXPIRY_SECONDS
end

-- UpdateAsync transform bodies. Each returns (newValue, newMeta), or nil to cancel
-- the write. They never yield, as UpdateAsync requires.

function ProfileLogic.acquire(current: any, meta: Meta?, lockId: string, now: number): (Profile?, Meta?)
	if ProfileLogic.isLockedByOther(meta, lockId, now) then
		return nil, nil
	end
	return ProfileLogic.reconcile(current), { lockId = lockId, lockedAt = now }
end

function ProfileLogic.save(profile: Profile, meta: Meta?, lockId: string, now: number, release: boolean): (Profile?, Meta?)
	if not meta or meta.lockId ~= lockId then
		-- Another server owns this profile now; writing would clobber its data.
		return nil, nil
	end
	if release then
		return profile, {}
	end
	return profile, { lockId = lockId, lockedAt = now }
end

-- Receipt ledger ---------------------------------------------------------------

function ProfileLogic.hasPurchase(profile: Profile, purchaseId: string): boolean
	return table.find(profile.purchaseLedger, purchaseId) ~= nil
end

function ProfileLogic.recordPurchase(profile: Profile, purchaseId: string)
	if ProfileLogic.hasPurchase(profile, purchaseId) then
		return
	end
	table.insert(profile.purchaseLedger, purchaseId)
	while #profile.purchaseLedger > ProfileLogic.LEDGER_LIMIT do
		table.remove(profile.purchaseLedger, 1)
	end
end

-- Retention bookkeeping ----------------------------------------------------------

function ProfileLogic.dayIndex(unixSeconds: number): number
	return math.floor(unixSeconds / 86400)
end

-- Records today's join. Returns the number of days since first join, and whether
-- this is the first join today (so return-visit analytics fire once per day).
function ProfileLogic.recordJoin(profile: Profile, unixSeconds: number): (number, boolean)
	local today = ProfileLogic.dayIndex(unixSeconds)
	if profile.firstJoinDay == nil then
		profile.firstJoinDay = today
	end
	local firstToday = table.find(profile.joinDays, today) == nil
	if firstToday then
		table.insert(profile.joinDays, today)
		table.sort(profile.joinDays)
		while #profile.joinDays > ProfileLogic.JOIN_DAYS_LIMIT do
			table.remove(profile.joinDays, 1)
		end
	end
	return today - (profile.firstJoinDay :: number), firstToday
end

-- Roblox-style day-N retention for one player: played on first day + n.
function ProfileLogic.returnedOnDay(profile: Profile, n: number): boolean
	if profile.firstJoinDay == nil then
		return false
	end
	return table.find(profile.joinDays, (profile.firstJoinDay :: number) + n) ~= nil
end

return ProfileLogic
