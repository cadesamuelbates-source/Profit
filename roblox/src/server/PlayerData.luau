--!strict
-- Session-locked player profiles on DataStoreService. All lock and merge
-- decisions live in Shared.ProfileLogic (pure, unit-tested). This module only
-- does I/O, retries and lifecycle.

local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local ProfileLogic = require(ReplicatedStorage.Shared.ProfileLogic)

type Profile = ProfileLogic.Profile

local PlayerData = {}

local STORE_NAME = "PlayerData_v1"
local AUTOSAVE_SECONDS = 180
local MAX_ATTEMPTS = 5
local LOCK_WAIT_ATTEMPTS = 6 -- about 30 s of waiting for another server to release

local lockId = HttpService:GenerateGUID(false)
local profiles: { [Player]: Profile } = {}
local loadedSignal = Instance.new("BindableEvent")

-- Studio without "Enable Studio Access to API Services" can't reach data stores.
-- Fall back to memory so the prototype is still playable; nothing persists then.
local okStore, storeOrErr = pcall(function()
	return DataStoreService:GetDataStore(STORE_NAME)
end)
local store: DataStore? = if okStore then storeOrErr :: DataStore else nil
PlayerData.memoryOnly = store == nil
if PlayerData.memoryOnly then
	warn("[PlayerData] Data stores unavailable; running memory-only:", storeOrErr)
end

local function keyFor(player: Player): string
	return "u_" .. tostring(player.UserId)
end

local function backoff(attempt: number)
	-- Exponential backoff with jitter, per Roblox data store guidance.
	task.wait(math.min(2 ^ attempt, 16) + math.random())
end

local function updateWithRetry(key: string, transform: (any, DataStoreKeyInfo?) -> (any, { number }?, any?)): boolean
	local s = store :: DataStore
	for attempt = 1, MAX_ATTEMPTS do
		local ok, err = pcall(function()
			s:UpdateAsync(key, transform)
		end)
		if ok then
			return true
		end
		warn(`[PlayerData] UpdateAsync failed ({attempt}/{MAX_ATTEMPTS}):`, err)
		backoff(attempt)
	end
	return false
end

function PlayerData.load(player: Player): Profile?
	if PlayerData.memoryOnly then
		local profile = ProfileLogic.default()
		profiles[player] = profile
		loadedSignal:Fire(player)
		return profile
	end
	for _ = 1, LOCK_WAIT_ATTEMPTS do
		local acquired: Profile? = nil
		local ok = updateWithRetry(keyFor(player), function(current, keyInfo)
			local meta = if keyInfo then keyInfo:GetMetadata() else nil
			local value, newMeta = ProfileLogic.acquire(current, meta, lockId, os.time())
			acquired = value
			if value == nil then
				return nil
			end
			return value, { player.UserId }, newMeta
		end)
		if not ok then
			return nil
		end
		if acquired then
			if player.Parent ~= Players then
				-- Left while loading: release immediately.
				PlayerData.saveProfile(player, acquired, true)
				return nil
			end
			profiles[player] = acquired
			loadedSignal:Fire(player)
			return acquired
		end
		task.wait(5) -- another server still holds the lock
	end
	return nil
end

function PlayerData.get(player: Player): Profile?
	return profiles[player]
end

-- Yields until the profile loads or the timeout passes. Used by the receipt handler.
function PlayerData.waitFor(player: Player, timeoutSeconds: number): Profile?
	local deadline = os.clock() + timeoutSeconds
	while not profiles[player] and player.Parent == Players and os.clock() < deadline do
		task.wait(0.25)
	end
	return profiles[player]
end

function PlayerData.saveProfile(player: Player, profile: Profile, release: boolean): boolean
	if PlayerData.memoryOnly then
		return true
	end
	local saved = false
	local ok = updateWithRetry(keyFor(player), function(_current, keyInfo)
		local meta = if keyInfo then keyInfo:GetMetadata() else nil
		local value, newMeta = ProfileLogic.save(profile, meta, lockId, os.time(), release)
		saved = value ~= nil
		if value == nil then
			return nil
		end
		return value, { player.UserId }, newMeta
	end)
	if ok and not saved then
		warn(`[PlayerData] Lost session lock for {player.UserId}; this server will not overwrite their data.`)
	end
	return ok and saved
end

function PlayerData.save(player: Player, release: boolean?): boolean
	local profile = profiles[player]
	if not profile then
		return false
	end
	return PlayerData.saveProfile(player, profile, release == true)
end

function PlayerData.release(player: Player)
	PlayerData.save(player, true)
	profiles[player] = nil
end

PlayerData.loaded = loadedSignal.Event

function PlayerData.start()
	task.spawn(function()
		while true do
			task.wait(AUTOSAVE_SECONDS)
			for player in profiles do
				task.spawn(PlayerData.save, player, false)
			end
		end
	end)
	game:BindToClose(function()
		-- Up to 30 s to finish; save everyone in parallel.
		local pending = 0
		for player in profiles do
			pending += 1
			task.spawn(function()
				PlayerData.save(player, true)
				pending -= 1
			end)
		end
		local deadline = os.clock() + 25
		while pending > 0 and os.clock() < deadline do
			task.wait(0.1)
		end
	end)
end

return PlayerData
