--!strict
-- Deterministic sale price. No randomness and no client inputs: the server feeds
-- it condition (C), staging score (S) and contributor count (n).
--
-- P = max(B + round(0.1V), round(V * (0.4 + 0.6C) * (1 + 0.3S) * (1 + 0.05(n-1))))

local Buyers = require("./Buyers")
local Houses = require("./Houses")

local SaleFormula = {}

-- Half-up rounding with a small epsilon so 312.4999999 (float noise for 312.5)
-- still rounds to 313, as the worked examples require.
function SaleFormula.round(x: number): number
	return math.floor(x + 0.5 + 1e-7)
end

local round = SaleFormula.round

local function clamp(x: number, lo: number, hi: number): number
	return math.max(lo, math.min(hi, x))
end

function SaleFormula.stagingScore(buyer: Buyers.Buyer, padStyles: { string? }, padCount: number): number
	if padCount <= 0 then
		return 0
	end
	local sum = 0
	for i = 1, padCount do
		sum += Buyers.taste(buyer, padStyles[i])
	end
	return clamp(sum / (2 * padCount), -0.5, 1)
end

function SaleFormula.crewMultiplier(n: number): number
	return 1 + 0.05 * (clamp(math.floor(n), 1, 4) - 1)
end

local function raw(tier: number, c: number, s: number, n: number): number
	local v = Houses.get(tier).value
	return v * (0.4 + 0.6 * clamp(c, 0, 1)) * (1 + 0.3 * clamp(s, -0.5, 1)) * SaleFormula.crewMultiplier(n)
end

local function floorPrice(tier: number): number
	local def = Houses.get(tier)
	return def.price + round(0.1 * def.value)
end

function SaleFormula.price(tier: number, c: number, s: number, n: number): number
	return math.max(floorPrice(tier), round(raw(tier, c, s, n)))
end

local function isOne(x: number): boolean
	return math.abs(x - 1) < 1e-9
end

function SaleFormula.tip(tier: number, c: number, s: number): number
	if isOne(c) and isOne(s) then
		return round(0.1 * Houses.get(tier).value)
	end
	return 0
end

export type Payout = { price: number, tip: number, total: number, ownerPay: number, helperPay: number }

function SaleFormula.payout(tier: number, c: number, s: number, n: number): Payout
	local price = SaleFormula.price(tier, c, s, n)
	local tip = SaleFormula.tip(tier, c, s)
	local total = price + tip
	local helperPay = 0
	if n > 1 then
		helperPay = round(0.5 * (total - Houses.get(tier).price))
	end
	return { price = price, tip = tip, total = total, ownerPay = total, helperPay = helperPay }
end

function SaleFormula.withDailyBonus(amount: number, eligible: boolean): number
	if eligible then
		return round(amount * 1.25)
	end
	return amount
end

function SaleFormula.reaction(c: number, s: number): "dream" | "jump" | "nod" | "scratch"
	if isOne(c) and isOne(s) then
		return "dream"
	elseif s >= 0.5 then
		return "jump"
	elseif s > 0 then
		return "nod"
	end
	return "scratch"
end

export type Breakdown = {
	base: number,
	repairs: number,
	staging: number,
	crew: number,
	floorApplied: boolean,
	price: number,
	tip: number,
	total: number,
}

-- Line items for the "Why this price" sign. `price` is authoritative; the lines
-- are rounded parts of the same formula and may differ from it by rounding.
function SaleFormula.breakdown(tier: number, c: number, s: number, n: number): Breakdown
	local v = Houses.get(tier).value
	local cc, ss = clamp(c, 0, 1), clamp(s, -0.5, 1)
	local afterRepairs = v * (0.4 + 0.6 * cc)
	local afterStaging = afterRepairs * (1 + 0.3 * ss)
	local afterCrew = afterStaging * SaleFormula.crewMultiplier(n)
	local price = SaleFormula.price(tier, c, s, n)
	local tip = SaleFormula.tip(tier, c, s)
	return {
		base = round(0.4 * v),
		repairs = round(0.6 * v * cc),
		staging = round(afterStaging - afterRepairs),
		crew = round(afterCrew - afterStaging),
		floorApplied = round(afterCrew) < floorPrice(tier),
		price = price,
		tip = tip,
		total = price + tip,
	}
end

return SaleFormula
