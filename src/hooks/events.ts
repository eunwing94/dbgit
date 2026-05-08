import type { ProcDefinition } from "../compare.js";
import type { EnvConfig } from "../config.js";

export type HookEventType = "before_compare" | "after_compare";

export type HookEvent =
  | {
      type: "before_compare";
      at: string;
      envs: EnvConfig[];
      proc: string;
    }
  | {
      type: "after_compare";
      at: string;
      envs: EnvConfig[];
      proc: string;
      results: Record<string, ProcDefinition>;
    };

