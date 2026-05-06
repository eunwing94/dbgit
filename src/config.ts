import process from "node:process";

export const DEFAULT_ENVS = ["PRD", "STG", "DEV", "QA"] as const;

export interface EnvConfig {
  name: string;
  host: string;
  port: number;
  user: string;
  password: string;
  database: string;
  driver: string;
}

function requireVar(value: string | undefined, key: string, envName: string): string {
  if (!value) {
    throw new Error(`${envName} 설정 누락: ${key}`);
  }
  return value;
}

export function loadEnvConfig(envName: string): EnvConfig {
  const prefix = envName.toUpperCase();
  const host = requireVar(process.env[`${prefix}_HOST`], `${prefix}_HOST`, envName);
  const portRaw = requireVar(process.env[`${prefix}_PORT`], `${prefix}_PORT`, envName);
  const user = requireVar(process.env[`${prefix}_USER`], `${prefix}_USER`, envName);
  const password = requireVar(process.env[`${prefix}_PASSWORD`], `${prefix}_PASSWORD`, envName);
  const database = requireVar(process.env[`${prefix}_DATABASE`], `${prefix}_DATABASE`, envName);
  const driver = process.env[`${prefix}_DRIVER`] ?? "ODBC Driver 18 for SQL Server";
  const port = parseInt(portRaw, 10);
  if (Number.isNaN(port)) {
    throw new Error(`${envName} PORT 형식 오류: ${portRaw}`);
  }
  return { name: prefix, host, port, user, password, database, driver };
}

export function loadEnvConfigs(names: string[]): EnvConfig[] {
  return names.map((n) => loadEnvConfig(n));
}
