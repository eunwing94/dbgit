/**
 * 훅 이벤트 타입 정의.
 *
 * 비교 전/후 시점에 전달할 컨텍스트를 정의합니다.
 */
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

