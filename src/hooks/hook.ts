import type { HookEvent } from "./events.js";

export interface Hook {
  onEvent(e: HookEvent): void;
}

export class LoggingHook implements Hook {
  onEvent(e: HookEvent): void {
    if (e.type === "before_compare") {
      console.error(`[dbgit] before_compare envs=${e.envs.length} proc=${e.proc}`);
    } else {
      console.error(
        `[dbgit] after_compare envs=${e.envs.length} proc=${e.proc} results=${Object.keys(e.results).length}`
      );
    }
  }
}

