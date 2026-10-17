--!strict
-- Repair-job rules. Pure: the server supplies time and validated player ids.

local JobLogic = {}

export type Spot = { id: string, kind: string, work: number, done: number, hitters: { [number]: boolean } }

-- Minimum seconds between accepted actions per player per job kind. Hold
-- durations are enforced client-side by ProximityPrompt, which exploiters can
-- skip, so these server caps are the real limit.
JobLogic.MIN_INTERVAL = {
	junk = 0.25,
	pipe = 0.3,
	patch = 0.8,
	window = 0.8,
	paint = 0.8,
	porch = 0.8,
	raccoon = 0.3,
	couch = 1.2,
	stage = 0.3,
} :: { [string]: number }

JobLogic.PIPE_PERIOD = 1.2
JobLogic.PIPE_TOLERANCE = 0.15
JobLogic.PIPE_ZONE_CAP = 0.9
JobLogic.COUCH_WINDOW = 5

function JobLogic.newSpot(id: string, kind: string, work: number): Spot
	return { id = id, kind = kind, work = work, done = 0, hitters = {} }
end

function JobLogic.isComplete(spot: Spot): boolean
	return spot.done >= spot.work
end

-- Work only moves forward. Returns (accepted, completedNow).
function JobLogic.applyHit(spot: Spot, userId: number, power: number): (boolean, boolean)
	if JobLogic.isComplete(spot) then
		return false, false
	end
	local inc = if spot.kind == "pipe" then 1 else math.max(1, math.floor(power))
	spot.done = math.min(spot.work, spot.done + inc)
	spot.hitters[userId] = true
	return true, JobLogic.isComplete(spot)
end

-- Finishes a spot in one action (solo couch drag, two-hand couch lift).
function JobLogic.completeSpot(spot: Spot, userId: number): boolean
	if JobLogic.isComplete(spot) then
		return false
	end
	spot.done = spot.work
	spot.hitters[userId] = true
	return true
end

function JobLogic.condition(spots: { Spot }): number
	local done, work = 0, 0
	for _, spot in spots do
		done += spot.done
		work += spot.work
	end
	if work == 0 then
		return 0
	end
	return done / work
end

-- Pipe timing bar --------------------------------------------------------------

-- Triangle wave: 0 at the sweep start, 1 at half a period, back to 0 at a full period.
function JobLogic.needlePosition(t: number, sweepStart: number): number
	local phase = ((t - sweepStart) % JobLogic.PIPE_PERIOD) / JobLogic.PIPE_PERIOD
	if phase <= 0.5 then
		return phase * 2
	end
	return 2 - phase * 2
end

function JobLogic.pipeZoneWidth(misses: number, onboarding: boolean, holdIt: boolean): number
	local width = (if onboarding then 0.40 else 0.25) + 0.10 * math.max(0, misses)
	if holdIt then
		width *= 2
	end
	return math.min(width, JobLogic.PIPE_ZONE_CAP)
end

-- True if the needle was inside the centered zone at any moment of
-- [arrival - tolerance, arrival]. The needle's range over an interval shorter
-- than half a period is spanned by its endpoint values plus any peak or trough
-- inside the interval, so this is exact rather than sampled.
function JobLogic.judgePipe(arrival: number, sweepStart: number, zoneWidth: number): boolean
	local period = JobLogic.PIPE_PERIOD
	local from = arrival - JobLogic.PIPE_TOLERANCE
	local p1 = JobLogic.needlePosition(from, sweepStart)
	local p2 = JobLogic.needlePosition(arrival, sweepStart)
	local lo, hi = math.min(p1, p2), math.max(p1, p2)
	local k = math.floor((from - sweepStart) / period)
	for i = k, k + 1 do
		local trough = sweepStart + i * period
		local peak = trough + period / 2
		if trough >= from and trough <= arrival then
			lo = 0
		end
		if peak >= from and peak <= arrival then
			hi = 1
		end
	end
	local zoneLo, zoneHi = 0.5 - zoneWidth / 2, 0.5 + zoneWidth / 2
	return hi >= zoneLo and lo <= zoneHi
end

-- Two-hand couch ----------------------------------------------------------------

export type Couch = { left: { userId: number, at: number }?, right: { userId: number, at: number }?, done: boolean }

function JobLogic.newCouch(): Couch
	return { left = nil, right = nil, done = false }
end

function JobLogic.liftCouch(couch: Couch, userId: number, side: "left" | "right", now: number): boolean
	if couch.done then
		return false
	end
	local grip = { userId = userId, at = now }
	local other
	if side == "left" then
		couch.left = grip
		other = couch.right
	else
		couch.right = grip
		other = couch.left
	end
	if other and other.userId ~= userId and now - other.at <= JobLogic.COUCH_WINDOW then
		couch.done = true
		return true
	end
	return false
end

-- Raccoon: three shoos, or one when another crew member blocks a different spot.
function JobLogic.shooRaccoon(spot: Spot, userId: number, pincer: boolean): boolean
	if JobLogic.isComplete(spot) then
		return false
	end
	spot.done = if pincer then spot.work else math.min(spot.work, spot.done + 1)
	spot.hitters[userId] = true
	return JobLogic.isComplete(spot)
end

return JobLogic
