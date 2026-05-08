/**
 * 출력 포맷(text/json/markdown).
 *
 * 비교 결과를 사람이 보기 좋게 렌더링합니다.
 */
import type { ProcDefinition } from "./compare.js";
import { digestOf } from "./compare.js";

export type OutputFormat = "text" | "json" | "markdown";

function diffEnvNames(baseline: string, definitions: Record<string, ProcDefinition>): string[] {
  const baseDigest = digestOf(definitions[baseline]!);
  return Object.entries(definitions)
    .filter(([, d]) => digestOf(d) !== baseDigest)
    .map(([n]) => n);
}

export function formatProcComparisonText(
  baseline: string,
  definitions: Record<string, ProcDefinition>
): string {
  const baseDef = definitions[baseline]!;
  const lines: string[] = [];
  lines.push(`기준 환경: ${baseline} (${baseDef.schema_name}.${baseDef.name})`);
  lines.push("");
  lines.push("환경별 결과:");
  for (const [envName, procDef] of Object.entries(definitions)) {
    const marker = digestOf(procDef) === digestOf(baseDef) ? "SAME" : "DIFF";
    lines.push(`- ${envName}: ${marker} (object_id=${procDef.object_id})`);
  }
  lines.push("");
  const diffEnvs = diffEnvNames(baseline, definitions);
  if (diffEnvs.length) {
    lines.push("차이나는 환경:");
    lines.push(diffEnvs.join(", "));
  } else {
    lines.push("모든 환경이 동일합니다.");
  }
  return lines.join("\n");
}

export function formatProcComparisonJson(
  baseline: string,
  definitions: Record<string, ProcDefinition>
): string {
  const baseDigest = digestOf(definitions[baseline]!);
  const envEntries: Record<string, object> = {};
  for (const [envName, procDef] of Object.entries(definitions)) {
    envEntries[envName] = {
      object_id: procDef.object_id,
      schema_name: procDef.schema_name,
      name: procDef.name,
      full_name: `${procDef.schema_name}.${procDef.name}`,
      digest: digestOf(procDef),
      same_as_baseline: digestOf(procDef) === baseDigest,
    };
  }
  const diff_environment_names = diffEnvNames(baseline, definitions);
  const payload = {
    baseline,
    target_full_name: `${definitions[baseline]!.schema_name}.${definitions[baseline]!.name}`,
    environments: envEntries,
    diff_environment_names,
    all_same: diff_environment_names.length === 0,
    definitions_with_body: Object.fromEntries(
      Object.entries(definitions).map(([k, v]) => [
        k,
        {
          object_id: v.object_id,
          schema_name: v.schema_name,
          name: v.name,
          full_name: `${v.schema_name}.${v.name}`,
          digest: digestOf(v),
          definition: v.definition,
        },
      ])
    ),
  };
  return JSON.stringify(payload, null, 2);
}

export function formatProcComparisonMarkdown(
  baseline: string,
  definitions: Record<string, ProcDefinition>
): string {
  const baseDef = definitions[baseline]!;
  const fn = `${baseDef.schema_name}.${baseDef.name}`;
  const lines: string[] = [
    "## 프로시저·함수 비교 결과",
    "",
    `- **기준 환경:** \`${baseline}\` — \`${fn}\``,
    "",
    "| 환경 | 상태 | object_id | full_name |",
    "|:--|:--|--:|:--|",
  ];
  for (const [envName, procDef] of Object.entries(definitions)) {
    const st = digestOf(procDef) === digestOf(baseDef) ? "SAME" : "DIFF";
    lines.push(`| ${envName} | ${st} | ${procDef.object_id} | \`${procDef.schema_name}.${procDef.name}\` |`);
  }
  lines.push("");
  const diffEnvs = diffEnvNames(baseline, definitions);
  if (diffEnvs.length) {
    lines.push(`**차이 환경:** ${diffEnvs.join(", ")}`);
  } else {
    lines.push("**모든 환경이 동일합니다.**");
  }
  return lines.join("\n");
}

export function formatProcComparison(
  baseline: string,
  definitions: Record<string, ProcDefinition>,
  fmt: OutputFormat
): string {
  if (fmt === "json") return formatProcComparisonJson(baseline, definitions);
  if (fmt === "markdown") return formatProcComparisonMarkdown(baseline, definitions);
  return formatProcComparisonText(baseline, definitions);
}
