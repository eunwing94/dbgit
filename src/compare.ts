/**
 * 비교 유스케이스.
 *
 * SQL Server에서 모듈 정의를 읽어 정규화/해시하여 SAME/DIFF를 판정합니다.
 */
import crypto from "node:crypto";
import sql from "mssql";
import type { EnvConfig } from "./config.js";
import { connectWithRetry } from "./db.js";

export interface ProcDefinition {
  object_id: number;
  schema_name: string;
  name: string;
  definition: string;
  normalized_definition: string;
}

export function digestOf(def: ProcDefinition): string {
  return crypto.createHash("sha256").update(def.normalized_definition, "utf8").digest("hex");
}

const PROC_QUERY = `
SELECT TOP 1
    o.object_id,
    s.name AS schema_name,
    o.name,
    m.definition
FROM sys.objects o
JOIN sys.sql_modules m ON o.object_id = m.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE o.type IN ('P', 'PC', 'FN', 'IF', 'TF')
  AND (
        o.object_id = @oid
        OR o.name = @pname
        OR s.name + '.' + o.name = @qual
  )
ORDER BY
    CASE WHEN o.object_id = @oid2 THEN 0 ELSE 1 END,
    o.name;
`;

function parseObjectId(procIdentifier: string): number | null {
  const n = parseInt(procIdentifier, 10);
  if (Number.isNaN(n)) return null;
  return n;
}

function normalizeDefinition(definition: string): string {
  return definition.replace(/\s+/g, "");
}

export async function fetchProcDefinition(
  config: EnvConfig,
  procIdentifier: string
): Promise<ProcDefinition> {
  const oid = parseObjectId(procIdentifier);
  const pool = await connectWithRetry(config);
  try {
    const req = pool.request();
    req.input("oid", sql.Int, oid ?? null);
    req.input("pname", sql.NVarChar(sql.MAX), procIdentifier);
    req.input("qual", sql.NVarChar(sql.MAX), procIdentifier);
    req.input("oid2", sql.Int, oid ?? null);
    const result = await req.query<{
      object_id: number;
      schema_name: string;
      name: string;
      definition: string | null;
    }>(PROC_QUERY);
    const row = result.recordset[0];
    if (!row) {
      throw new Error(`${config.name}에서 프로시저를 찾지 못했습니다: ${procIdentifier}`);
    }
    const definition = row.definition ?? "";
    const normalized_definition = normalizeDefinition(definition);
    return {
      object_id: row.object_id,
      schema_name: row.schema_name,
      name: row.name,
      definition,
      normalized_definition,
    };
  } finally {
    await pool.close();
  }
}

export async function compareAcrossEnvs(
  configs: EnvConfig[],
  procIdentifier: string
): Promise<Record<string, ProcDefinition>> {
  const results: Record<string, ProcDefinition> = {};
  for (const c of configs) {
    results[c.name] = await fetchProcDefinition(c, procIdentifier);
  }
  return results;
}
