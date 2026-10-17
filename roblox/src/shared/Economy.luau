--!strict
-- Coin transactions on a profile. Every function validates first and mutates
-- only on success, so a failed call leaves the profile unchanged.

local Catalog = require("./Catalog")
local Houses = require("./Houses")
local ProfileLogic = require("./ProfileLogic")
local SaleFormula = require("./SaleFormula")

type Profile = ProfileLogic.Profile

local Economy = {}

function Economy.ensureStarterKit(profile: Profile)
	for _, id in Catalog.STARTER_DECOR do
		profile.ownedDecor[id] = true
	end
	profile.ownedTools.basic = true
	profile.ownedCosmetics.hat_yellow = true
end

-- Is the Starter Shack free for this player right now?
-- Free on the first flip, and (soft-lock rescue, ACCEPTANCE A13a) whenever the
-- player can't afford it.
function Economy.starterIsFree(profile: Profile): boolean
	local firstFlip = profile.flipsCompleted == 0 and not profile.claimedFreeShack
	return firstFlip or profile.coins < Houses.get(1).price
end

-- Returns (ok, reason, pricePaid).
function Economy.buyListing(profile: Profile, tier: number): (boolean, string?, number?)
	local def = Houses.TIERS[tier]
	if not def then
		return false, "unknown_tier", nil
	end
	if tier > profile.unlockedTier then
		return false, "tier_locked", nil
	end
	if tier == 1 and Economy.starterIsFree(profile) then
		profile.claimedFreeShack = true
		return true, nil, 0
	end
	if profile.coins < def.price then
		return false, "not_enough_coins", nil
	end
	profile.coins -= def.price
	return true, nil, def.price
end

-- Buys a coin item (decor, tool, coin cosmetic). Robux passes are not bought here.
-- Returns (ok, reason, price).
function Economy.buyItem(profile: Profile, itemId: string): (boolean, string?, number?)
	local item = Catalog.shopItem(itemId)
	if not item or item.kind ~= "earned" then
		return false, "not_for_coins", nil
	end
	local price = item.coinPrice :: number
	if item.slot == "decor" then
		if profile.ownedDecor[itemId] then
			return false, "already_owned", nil
		end
	elseif item.slot == "tool" then
		local toolId = string.sub(itemId, 6) -- "tool_pro" -> "pro"
		local tool = Catalog.TOOLS[toolId]
		if not tool then
			return false, "not_for_coins", nil
		end
		if profile.ownedTools[toolId] then
			return false, "already_owned", nil
		end
		if profile.unlockedTier < tool.requiresTier then
			return false, "tier_locked", nil
		end
	else
		if profile.ownedCosmetics[itemId] then
			return false, "already_owned", nil
		end
	end
	if profile.coins < price then
		return false, "not_enough_coins", nil
	end
	profile.coins -= price
	if item.slot == "decor" then
		profile.ownedDecor[itemId] = true
	elseif item.slot == "tool" then
		profile.ownedTools[string.sub(itemId, 6)] = true
	else
		profile.ownedCosmetics[itemId] = true
	end
	return true, nil, price
end

-- Credits a sale payout, adding the first-flip-of-the-day bonus once per UTC day.
-- Returns (credited, bonusApplied).
function Economy.creditSale(profile: Profile, amount: number, utcDay: number): (number, boolean)
	local eligible = profile.lastBonusDay ~= utcDay
	local credited = SaleFormula.withDailyBonus(amount, eligible)
	if eligible then
		profile.lastBonusDay = utcDay
	end
	profile.coins += credited
	return credited, eligible
end

function Economy.recordFlip(profile: Profile, tier: number, price: number, buyerId: string, dream: boolean)
	profile.flipsCompleted += 1
	profile.unlockedTier = math.max(profile.unlockedTier, Houses.unlockedTier(profile.flipsCompleted))
	local key = tostring(tier)
	if price > (profile.bestPriceByTier[key] or 0) then
		profile.bestPriceByTier[key] = price
	end
	local entry = profile.buyerBook[buyerId] or { sold = false, dream = false }
	entry.sold = true
	entry.dream = entry.dream or dream
	profile.buyerBook[buyerId] = entry
end

return Economy
