package com.dbgit.app;

/**
 * 애플리케이션 오케스트레이터.
 *
 * - 유스케이스 서비스 호출을 감싸고
 * - 비교 전/후 Hook 이벤트를 발행합니다.
 */
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import com.dbgit.config.EnvConfig;
import com.dbgit.domain.ProcDefinition;
import com.dbgit.hooks.Hook;
import com.dbgit.hooks.HookEvent;
import com.dbgit.service.ProcCompareService;

public final class DbgitApp {

    private final ProcCompareService service;
    private final List<Hook> hooks;

    public DbgitApp(ProcCompareService service, List<Hook> hooks) {
        this.service = Objects.requireNonNull(service, "service");
        this.hooks = List.copyOf(hooks == null ? List.of() : hooks);
    }

    public Map<String, ProcDefinition> compareAll(List<EnvConfig> envs, String procIdentifier) {
        fire(HookEvent.beforeCompare(envs, procIdentifier));
        Map<String, ProcDefinition> out = new LinkedHashMap<>(service.compareAll(envs, procIdentifier));
        fire(HookEvent.afterCompare(envs, procIdentifier, out));
        return out;
    }

    private void fire(HookEvent e) {
        for (Hook h : hooks) {
            h.onEvent(e);
        }
    }
}

