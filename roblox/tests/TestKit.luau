--!strict
-- Minimal test harness for Lune: describe/it/expect with a non-zero exit on failure.

local TestKit = {}

local results = { passed = 0, failed = 0, failures = {} :: { string } }
local prefix: { string } = {}

local function fullName(name: string): string
	local parts = table.clone(prefix)
	table.insert(parts, name)
	return table.concat(parts, " > ")
end

function TestKit.describe(name: string, body: () -> ())
	table.insert(prefix, name)
	body()
	table.remove(prefix)
end

function TestKit.it(name: string, body: () -> ())
	local ok, err = pcall(body)
	if ok then
		results.passed += 1
	else
		results.failed += 1
		table.insert(results.failures, fullName(name) .. "\n    " .. tostring(err))
	end
end

local function render(value: any): string
	if type(value) == "table" then
		local keys = {}
		for k in value do
			table.insert(keys, k)
		end
		table.sort(keys, function(a, b)
			return tostring(a) < tostring(b)
		end)
		local parts = {}
		for _, k in keys do
			table.insert(parts, tostring(k) .. "=" .. render(value[k]))
		end
		return "{" .. table.concat(parts, ", ") .. "}"
	end
	return tostring(value)
end

local function deepEqual(a: any, b: any): boolean
	if type(a) ~= "table" or type(b) ~= "table" then
		return a == b
	end
	for k, v in a do
		if not deepEqual(v, b[k]) then
			return false
		end
	end
	for k in b do
		if a[k] == nil then
			return false
		end
	end
	return true
end

function TestKit.expect(actual: any)
	local api = {}
	function api.toBe(expected: any)
		if actual ~= expected then
			error(`expected {render(expected)}, got {render(actual)}`, 2)
		end
	end
	function api.toEqual(expected: any)
		if not deepEqual(actual, expected) then
			error(`expected {render(expected)}, got {render(actual)}`, 2)
		end
	end
	function api.toBeNear(expected: number, tolerance: number?)
		local tol = tolerance or 1e-9
		if type(actual) ~= "number" or math.abs(actual - expected) > tol then
			error(`expected ~{expected} (±{tol}), got {render(actual)}`, 2)
		end
	end
	function api.toBeTruthy()
		if not actual then
			error(`expected truthy, got {render(actual)}`, 2)
		end
	end
	function api.toBeFalsy()
		if actual then
			error(`expected falsy, got {render(actual)}`, 2)
		end
	end
	function api.toBeAtLeast(n: number)
		if type(actual) ~= "number" or actual < n then
			error(`expected >= {n}, got {render(actual)}`, 2)
		end
	end
	function api.toBeAtMost(n: number)
		if type(actual) ~= "number" or actual > n then
			error(`expected <= {n}, got {render(actual)}`, 2)
		end
	end
	function api.toThrow(fragment: string?)
		local ok, err = pcall(actual)
		if ok then
			error("expected function to throw", 2)
		end
		if fragment and not string.find(tostring(err), fragment, 1, true) then
			error(`expected error containing '{fragment}', got '{tostring(err)}'`, 2)
		end
	end
	return api
end

function TestKit.finish(): number
	for _, failure in results.failures do
		print("FAIL " .. failure)
	end
	print(`{results.passed} passed, {results.failed} failed`)
	return results.failed
end

return TestKit
