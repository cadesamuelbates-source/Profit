--!strict
-- First-time-user funnel. Step numbers and names are frozen: Creator Hub funnel
-- charts break if steps are renumbered after data exists.

local Onboarding = {}

Onboarding.STEPS = table.freeze({
	table.freeze({ step = 1, name = "Joined" }),
	table.freeze({ step = 2, name = "ArrivedAtLot" }),
	table.freeze({ step = 3, name = "ClaimedStarterShack" }),
	table.freeze({ step = 4, name = "FirstHit" }),
	table.freeze({ step = 5, name = "FirstSpotDone" }),
	table.freeze({ step = 6, name = "FirstPipeFixed" }),
	table.freeze({ step = 7, name = "HouseRepaired" }),
	table.freeze({ step = 8, name = "FirstDecorStaged" }),
	table.freeze({ step = 9, name = "FirstSale" }),
	table.freeze({ step = 10, name = "FirstShopPurchase" }),
	table.freeze({ step = 11, name = "SecondHouseBought" }),
})

Onboarding.LAST = #Onboarding.STEPS

local byName: { [string]: number } = {}
for _, entry in Onboarding.STEPS do
	byName[entry.name] = entry.step
end

function Onboarding.stepNumber(name: string): number
	local step = byName[name]
	if not step then
		error(`unknown onboarding step '{name}'`, 2)
	end
	return step
end

function Onboarding.stepName(step: number): string
	return Onboarding.STEPS[step].name
end

-- Forward only. Returns the new current step and every step to log, in order.
function Onboarding.advance(current: number, reached: number): (number, { number })
	if reached <= current then
		return current, {}
	end
	local target = math.min(reached, Onboarding.LAST)
	local steps = {}
	for step = current + 1, target do
		table.insert(steps, step)
	end
	return target, steps
end

function Onboarding.isComplete(current: number): boolean
	return current >= Onboarding.LAST
end

return Onboarding
