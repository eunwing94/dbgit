import test from "node:test";
import assert from "node:assert/strict";

import { parseEnvList } from "../dist/cli/envs.js";

test("parseEnvList trims and uppercases", () => {
  assert.deepEqual(parseEnvList(" prd, stg,DEV ,, qa "), ["PRD", "STG", "DEV", "QA"]);
});

