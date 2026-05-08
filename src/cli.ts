#!/usr/bin/env node
import fs from "node:fs";
import process from "node:process";
import { Command } from "commander";
import dotenv from "dotenv";
import { DEFAULT_ENVS, loadEnvConfigs } from "./config.js";
import { compareAcrossEnvs } from "./compare.js";
import { formatProcComparison, type OutputFormat } from "./outputFormat.js";
import { parseEnvList, requireBaselineIncluded } from "./cli/envs.js";
import { LoggingHook } from "./hooks/hook.js";
import type { HookEvent } from "./hooks/events.js";

async function main(): Promise<number> {
  const program = new Command();
  program
    .name("dbgit")
    .description("환경별 프로시저/함수 정의 차이를 확인합니다.")
    .argument("<proc>", "프로시저/함수 object_id 또는 이름 (schema.name 권장)")
    .option(
      "--envs <list>",
      "비교할 환경 (콤마 구분)",
      DEFAULT_ENVS.join(",")
    )
    .option("--baseline <name>", "기준 환경", "PRD")
    .option("--dotenv <path>", "환경변수 파일", ".env")
    .option("-o, --output <fmt>", "출력 형식", "text")
    .addHelpText(
      "after",
      "\n출력 형식: text | json | markdown"
    );

  program.parse(process.argv);
  const opts = program.opts<{ envs: string; baseline: string; dotenv: string; output: string }>();
  const procArg = program.args[0]!;
  const dotenvPath = opts.dotenv;
  if (fs.existsSync(dotenvPath)) {
    dotenv.config({ path: dotenvPath, override: true });
  }

  const envList = parseEnvList(opts.envs);
  const baseline = opts.baseline.trim().toUpperCase();
  try {
    requireBaselineIncluded(envList, baseline);
  } catch (e) {
    console.error((e as Error).message);
    return 1;
  }

  const out = opts.output as OutputFormat;
  if (!["text", "json", "markdown"].includes(out)) {
    console.error("output은 text, json, markdown 중 하나여야 합니다.");
    return 1;
  }

  try {
    const configs = loadEnvConfigs(envList);
    const hooks = [new LoggingHook()];
    const before: HookEvent = {
      type: "before_compare",
      at: new Date().toISOString(),
      envs: configs,
      proc: procArg,
    };
    for (const h of hooks) h.onEvent(before);
    const definitions = await compareAcrossEnvs(configs, procArg);
    const after: HookEvent = {
      type: "after_compare",
      at: new Date().toISOString(),
      envs: configs,
      proc: procArg,
      results: definitions,
    };
    for (const h of hooks) h.onEvent(after);
    console.log(formatProcComparison(baseline, definitions, out));
    return 0;
  } catch (e) {
    console.error("오류:", e);
    return 1;
  }
}

main().then((c) => process.exit(c));
