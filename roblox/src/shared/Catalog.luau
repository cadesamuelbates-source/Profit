--!strict
-- Everything a player can own. Robux items are cosmetic game passes, and every
-- one of them has a coin-earned alternative in the same slot (checked by ShopRules).

local ShopRules = require("./ShopRules")

local Catalog = {}

export type Decor = { id: string, name: string, style: string, shape: string }
export type Tool = { power: number, price: number, requiresTier: number }

Catalog.STYLES = { "Cozy", "Modern", "Rustic", "Bright" }
Catalog.SHAPES = { "Rug", "Lamp", "Plant", "Chair", "Art" }
Catalog.DECOR_PRICE = 150

-- Colors used to draw decor primitives, one per style.
Catalog.STYLE_COLORS = {
	Cozy = { 196, 120, 84 },
	Modern = { 90, 99, 112 },
	Rustic = { 140, 101, 61 },
	Bright = { 245, 196, 66 },
} :: { [string]: { number } }

Catalog.DECOR = {} :: { Decor }
local decorById: { [string]: Decor } = {}
for _, style in Catalog.STYLES do
	for _, shape in Catalog.SHAPES do
		local item = {
			id = string.lower(style) .. "_" .. string.lower(shape),
			name = `{style} {string.lower(shape)}`,
			style = style,
			shape = shape,
		}
		table.insert(Catalog.DECOR, item)
		decorById[item.id] = item
	end
end

Catalog.STARTER_DECOR = { "cozy_rug", "cozy_lamp", "bright_plant", "modern_chair", "rustic_chair" }

Catalog.TOOLS = {
	basic = { power = 1, price = 0, requiresTier = 1 },
	pro = { power = 2, price = 600, requiresTier = 2 },
	master = { power = 3, price = 2000, requiresTier = 3 },
} :: { [string]: Tool }

function Catalog.decor(id: string): Decor?
	return decorById[id]
end

function Catalog.isStarterDecor(id: string): boolean
	return table.find(Catalog.STARTER_DECOR, id) ~= nil
end

function Catalog.toolPower(ownedTools: { [string]: boolean }): number
	local power = Catalog.TOOLS.basic.power
	for id, owned in ownedTools do
		local tool = Catalog.TOOLS[id]
		if owned and tool and tool.power > power then
			power = tool.power
		end
	end
	return power
end

-- Shop entries (ShopRules.Item). Decor and tools are earned with coins; three
-- cosmetic game passes are listed with passId 0 until set up in Creator Hub.
Catalog.SHOP = {} :: { ShopRules.Item }

for _, item in Catalog.DECOR do
	if not Catalog.isStarterDecor(item.id) then
		table.insert(Catalog.SHOP, {
			id = item.id,
			name = item.name,
			kind = "earned",
			slot = "decor",
			gameplayEffect = "staging style",
			random = false,
			tradable = false,
			description = `A {string.lower(item.style)} {string.lower(item.shape)} for staging.`,
			coinPrice = Catalog.DECOR_PRICE,
		})
	end
end

for _, id in { "pro", "master" } do
	local tool = Catalog.TOOLS[id]
	table.insert(Catalog.SHOP, {
		id = "tool_" .. id,
		name = if id == "pro" then "Pro toolbelt" else "Master toolbelt",
		kind = "earned",
		slot = "tool",
		gameplayEffect = `repair power {tool.power}`,
		random = false,
		tradable = false,
		description = `Each hit counts as {tool.power}. Unlocks with tier {tool.requiresTier} houses.`,
		coinPrice = tool.price,
	})
end

-- Coin-earned cosmetics: house paint colors, hard-hat colors and a lot prop.
Catalog.PAINT_COLORS = {
	paint_sage = { name = "Sage paint", rgb = { 158, 186, 150 } },
	paint_sky = { name = "Sky paint", rgb = { 160, 200, 230 } },
	paint_cream = { name = "Cream paint", rgb = { 240, 228, 200 } },
	paint_coral = { name = "Coral paint", rgb = { 235, 140, 120 } },
	paint_slate = { name = "Slate paint", rgb = { 110, 122, 136 } },
	paint_sunny = { name = "Sunny paint", rgb = { 250, 215, 110 } },
} :: { [string]: { name: string, rgb: { number } } }

Catalog.HAT_COLORS = {
	hat_yellow = { name = "Yellow hard hat", rgb = { 245, 200, 40 }, free = true },
	hat_orange = { name = "Orange hard hat", rgb = { 240, 130, 40 } },
	hat_green = { name = "Green hard hat", rgb = { 90, 170, 90 } },
} :: { [string]: { name: string, rgb: { number }, free: boolean? } }

local paintIds = {}
for id in Catalog.PAINT_COLORS do
	table.insert(paintIds, id)
end
table.sort(paintIds)
for _, id in paintIds do
	table.insert(Catalog.SHOP, {
		id = id,
		name = Catalog.PAINT_COLORS[id].name,
		kind = "earned",
		slot = "paint",
		gameplayEffect = "none",
		random = false,
		tradable = false,
		description = "Changes the color your crew paints walls.",
		coinPrice = 200,
	})
end
for _, id in { "hat_orange", "hat_green" } do
	table.insert(Catalog.SHOP, {
		id = id,
		name = Catalog.HAT_COLORS[id].name,
		kind = "earned",
		slot = "hat",
		gameplayEffect = "none",
		random = false,
		tradable = false,
		description = "A hard hat color for your avatar.",
		coinPrice = 300,
	})
end
table.insert(Catalog.SHOP, {
	id = "prop_mailbox_red",
	name = "Red mailbox",
	kind = "earned",
	slot = "lot_prop",
	gameplayEffect = "none",
	random = false,
	tradable = false,
	description = "A mailbox for your lot.",
	coinPrice = 250,
})

-- Cosmetic game passes. passId 0 means "not created yet": the shop shows them
-- as unavailable and never prompts. Prices are never written here; the client
-- fetches them from MarketplaceService because regional pricing varies.
Catalog.PASSES = {
	{
		id = "pass_crew_hats",
		name = "Crew hard hats",
		kind = "gamepass",
		slot = "hat",
		gameplayEffect = "none",
		random = false,
		tradable = false,
		description = "Five hard hat and vest color sets. All five are shown here.",
		passId = 0,
	},
	{
		id = "pass_pastel_paint",
		name = "Pastel paint pack",
		kind = "gamepass",
		slot = "paint",
		gameplayEffect = "none",
		random = false,
		tradable = false,
		description = "Six pastel house paint colors. Paint color never changes what a buyer pays.",
		passId = 0,
	},
	{
		id = "pass_lot_props",
		name = "Lot mailbox and flag set",
		kind = "gamepass",
		slot = "lot_prop",
		gameplayEffect = "none",
		random = false,
		tradable = false,
		description = "A mailbox and flag for your own lot. Not used for staging.",
		passId = 0,
	},
} :: { ShopRules.Item }

for _, pass in Catalog.PASSES do
	table.insert(Catalog.SHOP, pass)
end

local shopById: { [string]: ShopRules.Item } = {}
for _, item in Catalog.SHOP do
	shopById[item.id] = item
end

function Catalog.shopItem(id: string): ShopRules.Item?
	return shopById[id]
end

return Catalog
