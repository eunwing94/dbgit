import process from "node:process";
import { setTimeout as delay } from "node:timers/promises";
import sql from "mssql";
import type { EnvConfig } from "./config.js";

const RETRIES_ENV = "DBGIT_DB_MAX_RETRIES";
const DELAY_ENV = "DBGIT_DB_RETRY_DELAY_SEC";

function retryParams(): { max: number; delaySec: number } {
  const max = Math.max(1, parseInt(process.env[RETRIES_ENV] ?? "3", 10) || 3);
  const delaySec = Math.max(0, parseFloat(process.env[DELAY_ENV] ?? "1.0") || 1.0);
  return { max, delaySec };
}

export function buildPoolConfig(config: EnvConfig): sql.config {
  return {
    user: config.user,
    password: config.password,
    server: config.host,
    port: config.port,
    database: config.database,
    options: {
      encrypt: true,
      trustServerCertificate: true,
    },
    connectionTimeout: 5000,
    requestTimeout: 60000,
  };
}

/** 단일 연결 풀 생성 후 재시도. 사용 후 pool.close() 호출 권장. */
export async function connectWithRetry(cfg: EnvConfig): Promise<sql.ConnectionPool> {
  const { max, delaySec } = retryParams();
  let lastErr: unknown;
  for (let attempt = 1; attempt <= max; attempt++) {
    try {
      const pool = new sql.ConnectionPool(buildPoolConfig(cfg));
      await pool.connect();
      return pool;
    } catch (e) {
      lastErr = e;
      console.error(`DB 연결 실패 env=${cfg.name} 시도 ${attempt}/${max}:`, e);
      if (attempt < max && delaySec > 0) {
        await delay(delaySec * 1000);
      }
    }
  }
  throw lastErr;
}
