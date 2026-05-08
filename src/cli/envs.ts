export function parseEnvList(s: string): string[] {
  return (s ?? "")
    .split(",")
    .map((x) => x.trim().toUpperCase())
    .filter(Boolean);
}

export function requireBaselineIncluded(envs: string[], baseline: string): void {
  if (!envs.includes(baseline)) {
    throw new Error("baseline 환경이 envs 목록에 포함되어야 합니다.");
  }
}

