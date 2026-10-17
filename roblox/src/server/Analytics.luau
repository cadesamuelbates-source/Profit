--!strict
-- AnalyticsService adapter. Uses only the current Log* methods (the Fire* ones are
-- deprecated). Roblox accepts events only from published servers, never from
-- Studio, so in Studio events are counted locally and printed for checking.

local AnalyticsService = game:GetService("AnalyticsService")
local RunService = game:GetService("RunService")

local Analytics = {}

local live = not RunService:IsStudio()
local localCounts: { [string]: number } = {}
Analytics.verbose = RunService:IsStudio()

local function record(key: string)
	localCounts[key] = (localCounts[key] or 0) + 1
	if Analytics.verbose then
		print("[Analytics]", key)
	end
end

local function send(method: string, ...: any)
	if not live then
		return
	end
	local args = table.pack(...)
	local ok, err = pcall(function()
		(AnalyticsService :: any)[method](AnalyticsService, table.unpack(args, 1, args.n))
	end)
	if not ok then
		warn(`[Analytics] {method} failed:`, err)
	end
end

-- Steps are 1..100 and must never be renumbered once data exists.
function Analytics.onboardingStep(player: Player, step: number, stepName: string)
	record(`onboarding:{step}:{stepName}`)
	send("LogOnboardingFunnelStepEvent", player, step, stepName)
end

-- One funnel session per house flip, so repeated flips are separate sessions.
function Analytics.flipStep(player: Player, flipSessionId: string, step: number, stepName: string)
	record(`flip:{step}:{stepName}`)
	send("LogFunnelStepEvent", player, "HouseFlip", flipSessionId, step, stepName)
end

-- flow: "Source" or "Sink". transactionType: an Enum.AnalyticsEconomyTransactionType name.
function Analytics.economy(player: Player, flow: "Source" | "Sink", amount: number, endingBalance: number,
	transactionType: string, itemSku: string)
	if amount <= 0 then
		return -- the API requires a positive amount
	end
	record(`economy:{flow}:{transactionType}:{itemSku}`)
	local flowType = if flow == "Source" then Enum.AnalyticsEconomyFlowType.Source else Enum.AnalyticsEconomyFlowType.Sink
	send("LogEconomyEvent", player, flowType, "Coins", amount, math.max(0, endingBalance), transactionType, itemSku)
end

-- Up to 100 distinct event names per experience: keep this list short and fixed.
function Analytics.custom(player: Player, eventName: string, value: number?)
	record(`custom:{eventName}`)
	send("LogCustomEvent", player, eventName, value or 1)
end

-- Our own D1/D7 proxy, because the Creator Hub retention dashboard only unlocks
-- after >10 DAU and 10 play hours for 7 consecutive days.
function Analytics.returnVisit(player: Player, daysSinceFirstJoin: number)
	Analytics.custom(player, "ReturnVisitDay", daysSinceFirstJoin)
end

function Analytics.localCounts(): { [string]: number }
	return table.clone(localCounts)
end

return Analytics
