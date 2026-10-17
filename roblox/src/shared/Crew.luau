--!strict
-- A crew is the set of players working one lot. Joining is always the player's
-- choice; nobody is auto-joined.

local Crew = {}

Crew.MAX_MEMBERS = 4

export type Mode = "Open" | "Friends" | "Solo"
export type CrewState = {
	ownerId: number,
	mode: Mode,
	members: { number },
	contributors: { [number]: boolean },
}

function Crew.new(ownerId: number, mode: Mode): CrewState
	return { ownerId = ownerId, mode = mode, members = { ownerId }, contributors = {} }
end

function Crew.isMember(crew: CrewState, userId: number): boolean
	return table.find(crew.members, userId) ~= nil
end

function Crew.canJoin(crew: CrewState, userId: number, isFriend: boolean): (boolean, string?)
	if Crew.isMember(crew, userId) then
		return false, "already_member"
	end
	if #crew.members >= Crew.MAX_MEMBERS then
		return false, "crew_full"
	end
	if crew.mode == "Solo" then
		return false, "solo_lot"
	end
	if crew.mode == "Friends" and not isFriend then
		return false, "friends_only"
	end
	return true, nil
end

function Crew.join(crew: CrewState, userId: number)
	if not Crew.isMember(crew, userId) and #crew.members < Crew.MAX_MEMBERS then
		table.insert(crew.members, userId)
	end
end

-- Leaving forfeits contribution: pay goes to people present at the sale.
function Crew.leave(crew: CrewState, userId: number)
	if userId == crew.ownerId then
		return
	end
	local index = table.find(crew.members, userId)
	if index then
		table.remove(crew.members, index)
	end
	crew.contributors[userId] = nil
end

function Crew.setMode(crew: CrewState, mode: Mode)
	crew.mode = mode
end

function Crew.markContributor(crew: CrewState, userId: number)
	if Crew.isMember(crew, userId) then
		crew.contributors[userId] = true
	end
end

function Crew.contributorCount(crew: CrewState): number
	local n = 0
	for _ in crew.contributors do
		n += 1
	end
	return math.clamp(n, 1, Crew.MAX_MEMBERS)
end

function Crew.helpers(crew: CrewState): { number }
	local list = {}
	for userId in crew.contributors do
		if userId ~= crew.ownerId then
			table.insert(list, userId)
		end
	end
	table.sort(list)
	return list
end

-- Clears per-house state after a sale; membership stays.
function Crew.resetContributors(crew: CrewState)
	crew.contributors = {}
end

return Crew
