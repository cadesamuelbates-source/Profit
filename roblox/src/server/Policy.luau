--!strict
-- Cached PolicyService lookups. Fails closed: if the lookup errors, treat the
-- player as restricted. The game ships no paid random items and no trading, so
-- these flags gate nothing today; they're checked so a future feature can't
-- forget to.

local PolicyService = game:GetService("PolicyService")

local Policy = {}

export type Info = {
	ArePaidRandomItemsRestricted: boolean,
	IsPaidItemTradingAllowed: boolean,
	AreAdsAllowed: boolean,
}

local RESTRICTED: Info = {
	ArePaidRandomItemsRestricted = true,
	IsPaidItemTradingAllowed = false,
	AreAdsAllowed = false,
}

local cache: { [Player]: Info } = {}

function Policy.get(player: Player): Info
	local cached = cache[player]
	if cached then
		return cached
	end
	local ok, result = pcall(function()
		return PolicyService:GetPolicyInfoForPlayerAsync(player)
	end)
	local info = RESTRICTED
	if ok and type(result) == "table" then
		info = {
			ArePaidRandomItemsRestricted = result.ArePaidRandomItemsRestricted ~= false,
			IsPaidItemTradingAllowed = result.IsPaidItemTradingAllowed == true,
			AreAdsAllowed = result.AreAdsAllowed == true,
		}
	end
	cache[player] = info
	return info
end

function Policy.forget(player: Player)
	cache[player] = nil
end

return Policy
