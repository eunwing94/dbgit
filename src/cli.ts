#!/usr/bin/env node
import fs from "node:fs";
import process from "node:process";
import { Command } from "commander";
import dotenv from "dotenv";
import { DEFAULT_ENVS, loadEnvConfigs } from "./config.js";
import { compareAcrossEnvs } from "./compare.js";
import { formatProcComparison, type OutputFormat } from "./outputFormat.js";

function parseEnvList(s: string): string[] {
  return s
    .split(",")
    .map((x) => x.trim().toUpperCase())
    .filter(Boolean);
}

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
  if (!envList.includes(baseline)) {
    console.error("baseline 환경이 envs 목록에 포함되어야 합니다.");
    return 1;
  }

  const out = opts.output as OutputFormat;
  if (!["text", "json", "markdown"].includes(out)) {
    console.error("output은 text, json, markdown 중 하나여야 합니다.");
    return 1;
  }

  try {
    const configs = loadEnvConfigs(envList);
    const definitions = await compareAcrossEnvs(configs, procArg);
    console.log(formatProcComparison(baseline, definitions, out));
    return 0;
  } catch (e) {
    console.error("오류:", e);
    return 1;
  }
}

main().then((c) => process.exit(c));
