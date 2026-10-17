-- Runs every spec and exits non-zero on any failure: `lune run tests/run.luau`
local process = require("@lune/process")
local TestKit = require("./TestKit")

require("./ProfileLogic.spec")
require("./ShopRules.spec")
require("./Game.spec")

process.exit(TestKit.finish())
