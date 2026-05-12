/**
 * 등록된 훅을 순서대로 실행하는 미들웨어.
 */
import type { HookEvent } from "./events.js";
import type { Hook } from "./hook.js";

export class HookPipeline {
  constructor(private readonly hooks: Hook[]) {}

  run(e: HookEvent): void {
    for (const h of this.hooks) {
      h.onEvent(e);
    }
  }
}
