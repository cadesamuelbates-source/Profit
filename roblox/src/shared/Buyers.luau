--!strict
-- The fixed buyer pool. Each buyer's taste is shown on the listing before purchase.

local Buyers = {}

export type Buyer = { id: string, name: string, love: string, like: string, dislike: string }

Buyers.STYLES = { "Cozy", "Modern", "Rustic", "Bright" }

-- Each style is loved by exactly two buyers.
Buyers.POOL = {
	{ id = "rosa", name = "Rosa", love = "Cozy", like = "Bright", dislike = "Modern" },
	{ id = "ivy", name = "Ivy", love = "Cozy", like = "Rustic", dislike = "Bright" },
	{ id = "max", name = "Max", love = "Modern", like = "Bright", dislike = "Rustic" },
	{ id = "sam", name = "Sam", love = "Modern", like = "Rustic", dislike = "Cozy" },
	{ id = "june", name = "June", love = "Rustic", like = "Cozy", dislike = "Modern" },
	{ id = "lena", name = "Lena", love = "Rustic", like = "Bright", dislike = "Cozy" },
	{ id = "theo", name = "Theo", love = "Bright", like = "Modern", dislike = "Cozy" },
	{ id = "kai", name = "Kai", love = "Bright", like = "Cozy", dislike = "Rustic" },
} :: { Buyer }

local byId: { [string]: Buyer } = {}
for _, buyer in Buyers.POOL do
	byId[buyer.id] = buyer
end

function Buyers.get(id: string): Buyer?
	return byId[id]
end

function Buyers.taste(buyer: Buyer, style: string?): number
	if style == nil then
		return 0
	elseif style == buyer.love then
		return 2
	elseif style == buyer.like then
		return 1
	elseif style == buyer.dislike then
		return -1
	end
	return 0
end

return Buyers
