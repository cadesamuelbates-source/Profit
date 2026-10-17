local T = require("./TestKit")
local ShopRules = require("../src/shared/ShopRules")

local describe, it, expect = T.describe, T.it, T.expect

local function item(overrides: { [string]: any })
	local base = {
		id = "paint_teal",
		name = "Teal paint",
		kind = "earned",
		slot = "paint",
		gameplayEffect = "none",
		random = false,
		tradable = false,
		description = "A calm teal for walls.",
		coinPrice = 50,
	}
	for k, v in overrides do
		base[k] = v
	end
	return base
end

local function hasProblem(problems: { string }, fragment: string): boolean
	for _, p in problems do
		if string.find(p, fragment, 1, true) then
			return true
		end
	end
	return false
end

describe("ShopRules.validateCatalog", function()
	it("accepts a fair cosmetic catalog", function()
		local problems = ShopRules.validateCatalog({
			item({}),
			item({ id = "pack_pastel", name = "Pastel paint set", kind = "gamepass", coinPrice = nil, passId = 0 }),
		})
		expect(#problems).toBe(0)
	end)

	it("rejects random, tradable and pay-to-win items", function()
		local problems = ShopRules.validateCatalog({
			item({ id = "a", random = true }),
			item({ id = "b", tradable = true }),
			item({ id = "c", kind = "gamepass", gameplayEffect = "2x coins" }),
		})
		expect(hasProblem(problems, "random outcomes")).toBeTruthy()
		expect(hasProblem(problems, "trading")).toBeTruthy()
		expect(hasProblem(problems, "must not affect gameplay")).toBeTruthy()
	end)

	it("rejects consumable developer products", function()
		expect(hasProblem(ShopRules.validateCatalog({ item({ kind = "devproduct", productId = 1 }) }), "developer products"))
			.toBeTruthy()
	end)

	it("rejects pressure wording but not innocent words", function()
		local bad = ShopRules.validateCatalog({
			item({ id = "x", name = "Get it NOW" }),
			item({ id = "y", description = "Limited time" }),
			item({ id = "z", description = "Only for today!" }),
			item({ id = "w", name = "Mystery box" }),
		})
		expect(#bad).toBeAtLeast(4)
		local ok = ShopRules.validateCatalog({ item({ name = "Snow white paint", description = "Known for its glow." }) })
		expect(#ok).toBe(0)
	end)

	it("rejects hard-coded Robux prices in text", function()
		expect(hasProblem(ShopRules.validateCatalog({ item({ description = "Costs 49 Robux" }) }), "MarketplaceService"))
			.toBeTruthy()
	end)

	it("rejects duplicate ids and earned items without a coin price", function()
		local problems = ShopRules.validateCatalog({ item({}), item({}), item({ id = "free", coinPrice = 0 }) })
		expect(hasProblem(problems, "duplicate id")).toBeTruthy()
		expect(hasProblem(problems, "positive coin price")).toBeTruthy()
	end)
end)

describe("ShopRules.slotsWithoutEarnedOption", function()
	it("flags a slot that can only be bought", function()
		local missing = ShopRules.slotsWithoutEarnedOption({
			item({}),
			item({ id = "hat_gold", slot = "hat", kind = "gamepass", coinPrice = nil }),
		})
		expect(missing).toEqual({ "hat" })
	end)
end)

describe("ShopRules.priceLabel", function()
	it("never invents a price", function()
		expect(ShopRules.priceLabel(nil)).toBe("Price unavailable")
		expect(ShopRules.priceLabel(75)).toBe("75 Robux")
	end)
end)

return nil
