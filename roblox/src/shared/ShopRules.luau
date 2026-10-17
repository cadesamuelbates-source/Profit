--!strict
-- Kid-safe monetization rules as executable checks. The catalog in Config must
-- pass validateCatalog() (unit-tested, and checked again at server start).
--
-- Sources: Roblox monetization presentation rules (no false scarcity, no
-- countdowns, no pushy language with minors), paid-random-items policy,
-- regional pricing (never hard-code Robux prices in UI), Advertising Standards
-- wording (no "only"/"just", no urging children to buy).

local ShopRules = {}

export type Item = {
	id: string,
	name: string,
	kind: "gamepass" | "devproduct" | "earned",
	slot: string,
	gameplayEffect: string, -- must be "none" for anything sold for Robux
	random: boolean,
	tradable: boolean,
	description: string,
	coinPrice: number?, -- earned items only
	passId: number?, -- configured in Creator Hub; 0 means "not set up yet"
	productId: number?,
}

-- Phrases that pressure or mislead; checked case-insensitively in names and
-- descriptions. Buttons use the fixed label "See price".
ShopRules.BANNED_PHRASES = {
	"now",
	"hurry",
	"last chance",
	"limited",
	"only",
	"just",
	"sale",
	"% off",
	"ends in",
	"today only",
	"ask your parent",
	"best value",
	"exclusive",
	"rare",
	"mystery",
	"surprise",
	"!",
}

ShopRules.BUY_BUTTON_LABEL = "See price"

local function containsBanned(text: string): string?
	local lower = string.lower(text)
	for _, phrase in ShopRules.BANNED_PHRASES do
		if string.find(lower, phrase, 1, true) then
			-- "now" inside a longer word (e.g. "snow") is fine; check word boundaries for alphabetic phrases.
			if string.match(phrase, "^%a+$") then
				if string.find(" " .. lower .. " ", "[^%a]" .. phrase .. "[^%a]") then
					return phrase
				end
			else
				return phrase
			end
		end
	end
	return nil
end

-- Returns a list of human-readable violations (empty means the catalog passes).
function ShopRules.validateCatalog(items: { Item }): { string }
	local problems = {}
	local seen = {}
	for _, item in items do
		local where = `item '{item.id}'`
		if seen[item.id] then
			table.insert(problems, `{where}: duplicate id`)
		end
		seen[item.id] = true
		if item.random then
			table.insert(problems, `{where}: random outcomes are not allowed`)
		end
		if item.tradable then
			table.insert(problems, `{where}: trading is not allowed`)
		end
		if item.kind ~= "earned" and item.gameplayEffect ~= "none" then
			table.insert(problems, `{where}: items sold for Robux must not affect gameplay ({item.gameplayEffect})`)
		end
		if item.kind == "earned" and (type(item.coinPrice) ~= "number" or (item.coinPrice :: number) <= 0) then
			table.insert(problems, `{where}: earned items need a positive coin price`)
		end
		if item.kind == "devproduct" then
			-- Consumables invite repeat spending; this game sells only permanent cosmetics.
			table.insert(problems, `{where}: developer products (consumables) are not used in this game`)
		end
		for _, field in { "name", "description" } do
			local banned = containsBanned((item :: any)[field])
			if banned then
				table.insert(problems, `{where}: {field} uses pressure wording '{banned}'`)
			end
		end
		if string.find(item.description, "%d+%s*[Rr]obux") or string.find(item.description, "R%$") then
			table.insert(problems, `{where}: prices must come from MarketplaceService, not text`)
		end
	end
	return problems
end

-- Every cosmetic slot that is sold for Robux must also have at least one item
-- that can be earned with coins, so nobody is locked out of a slot.
function ShopRules.slotsWithoutEarnedOption(items: { Item }): { string }
	local earned, sold = {}, {}
	for _, item in items do
		if item.kind == "earned" then
			earned[item.slot] = true
		else
			sold[item.slot] = true
		end
	end
	local missing = {}
	for slot in sold do
		if not earned[slot] then
			table.insert(missing, slot)
		end
	end
	table.sort(missing)
	return missing
end

-- Text shown for a Robux price. `price` is nil until MarketplaceService answers;
-- it must never be a number typed into the catalog.
function ShopRules.priceLabel(price: number?): string
	if price == nil then
		return "Price unavailable"
	end
	return `{price} Robux`
end

return ShopRules
