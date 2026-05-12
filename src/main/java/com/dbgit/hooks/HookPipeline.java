package com.dbgit.hooks;

import java.util.List;
import java.util.Objects;

/**
 * 등록된 훅을 순서대로 실행하는 미들웨어.
 */
public final class HookPipeline {

    private final List<Hook> hooks;

    public HookPipeline(List<Hook> hooks) {
        this.hooks = List.copyOf(Objects.requireNonNullElse(hooks, List.of()));
    }

    public void run(HookEvent event) {
        for (Hook h : hooks) {
            h.onEvent(event);
        }
    }
}
