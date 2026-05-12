/**
 * 기본 훅 파이프라인 조립(팩토리).
 */
import { HookPipeline } from "./hooks/pipeline.js";
import { LoggingHook } from "./hooks/hook.js";

export function createDefaultHookPipeline(): HookPipeline {
  return new HookPipeline([new LoggingHook()]);
}
