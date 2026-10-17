--!strict
-- Listing Board contents: two houses per unlocked tier, each with its buyer
-- shown up front. The buyer draw is free (no Robux path reaches coins), so it is
-- not a paid random item.

local Buyers = require("./Buyers")
local Houses = require("./Houses")

local Listings = {}

export type Listing = { tier: number, buyerId: string, price: number, free: boolean }

Listings.PER_TIER = 2
Listings.ONBOARDING_BUYER = "rosa"

function Listings.generate(unlockedTier: number, randomInt: (number, number) -> number, freeStarter: boolean): { Listing }
	local listings = {}
	for tier = 1, math.clamp(unlockedTier, 1, Houses.MAX_TIER) do
		local used: { [string]: boolean } = {}
		for slot = 1, Listings.PER_TIER do
			local buyerId: string
			if tier == 1 and slot == 1 and freeStarter then
				buyerId = Listings.ONBOARDING_BUYER
			else
				buyerId = Buyers.POOL[randomInt(1, #Buyers.POOL)].id
				local attempts = 0
				while used[buyerId] and attempts < 8 do
					buyerId = Buyers.POOL[randomInt(1, #Buyers.POOL)].id
					attempts += 1
				end
			end
			used[buyerId] = true
			local free = tier == 1 and slot == 1 and freeStarter
			table.insert(listings, {
				tier = tier,
				buyerId = buyerId,
				price = if free then 0 else Houses.get(tier).price,
				free = free,
			})
		end
	end
	return listings
end

return Listings
