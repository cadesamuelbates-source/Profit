--!strict
-- House tiers and their repair spots. Work totals are computed from the spot list.

local Houses = {}

export type SpotGroup = { kind: string, count: number, work: number }
export type TierDef = {
	tier: number,
	name: string,
	value: number, -- V: fixed-up value
	price: number, -- B: listing price, 0.4 * V
	unlockFlips: number,
	pads: number,
	spots: { SpotGroup },
}

Houses.TIERS = {
	[1] = {
		tier = 1,
		name = "Starter Shack",
		value = 250,
		price = 100,
		unlockFlips = 0,
		pads = 3,
		spots = {
			{ kind = "junk", count = 3, work = 4 },
			{ kind = "pipe", count = 1, work = 3 },
			{ kind = "patch", count = 2, work = 3 },
			{ kind = "window", count = 2, work = 2 },
		},
	},
	[2] = {
		tier = 2,
		name = "Cozy Cottage",
		value = 600,
		price = 240,
		unlockFlips = 3,
		pads = 4,
		spots = {
			{ kind = "junk", count = 4, work = 4 },
			{ kind = "pipe", count = 1, work = 3 },
			{ kind = "patch", count = 3, work = 3 },
			{ kind = "window", count = 3, work = 2 },
			{ kind = "paint", count = 4, work = 3 },
			{ kind = "couch", count = 1, work = 3 },
			{ kind = "raccoon", count = 1, work = 3 },
		},
	},
	[3] = {
		tier = 3,
		name = "Family Bungalow",
		value = 1400,
		price = 560,
		unlockFlips = 8,
		pads = 5,
		spots = {
			{ kind = "junk", count = 5, work = 4 },
			{ kind = "pipe", count = 1, work = 3 },
			{ kind = "patch", count = 4, work = 3 },
			{ kind = "window", count = 4, work = 2 },
			{ kind = "paint", count = 6, work = 3 },
			{ kind = "couch", count = 1, work = 3 },
			{ kind = "raccoon", count = 1, work = 3 },
			{ kind = "porch", count = 4, work = 3 },
		},
	},
} :: { [number]: TierDef }

Houses.MAX_TIER = 3

function Houses.get(tier: number): TierDef
	local def = Houses.TIERS[tier]
	if not def then
		error(`unknown house tier {tostring(tier)}`, 2)
	end
	return def
end

function Houses.totalWork(tier: number): number
	local total = 0
	for _, group in Houses.get(tier).spots do
		total += group.count * group.work
	end
	return total
end

function Houses.spotList(tier: number): { { id: string, kind: string, work: number } }
	local list = {}
	for _, group in Houses.get(tier).spots do
		for i = 1, group.count do
			table.insert(list, { id = `{group.kind}_{i}`, kind = group.kind, work = group.work })
		end
	end
	return list
end

function Houses.unlockedTier(flipsCompleted: number): number
	local unlocked = 1
	for tier = 1, Houses.MAX_TIER do
		if flipsCompleted >= Houses.TIERS[tier].unlockFlips then
			unlocked = tier
		end
	end
	return unlocked
end

return Houses
