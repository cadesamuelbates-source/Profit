--!strict
-- Token-bucket rate limiter keyed by player and action. Pure: the caller passes
-- the clock, so tests are deterministic.

local RateLimiter = {}
RateLimiter.__index = RateLimiter

export type Limiter = typeof(setmetatable(
	{} :: { capacity: number, refillPerSecond: number, buckets: { [string]: { tokens: number, at: number } } },
	RateLimiter
))

function RateLimiter.new(capacity: number, refillPerSecond: number): Limiter
	return setmetatable({ capacity = capacity, refillPerSecond = refillPerSecond, buckets = {} }, RateLimiter)
end

function RateLimiter.allow(self: Limiter, key: string, now: number): boolean
	local bucket = self.buckets[key]
	if not bucket then
		bucket = { tokens = self.capacity, at = now }
		self.buckets[key] = bucket
	end
	local elapsed = math.max(0, now - bucket.at)
	bucket.tokens = math.min(self.capacity, bucket.tokens + elapsed * self.refillPerSecond)
	bucket.at = now
	if bucket.tokens >= 1 then
		bucket.tokens -= 1
		return true
	end
	return false
end

function RateLimiter.forget(self: Limiter, prefix: string)
	for key in self.buckets do
		if string.sub(key, 1, #prefix) == prefix then
			self.buckets[key] = nil
		end
	end
end

return RateLimiter
