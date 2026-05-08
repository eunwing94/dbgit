package com.dbgit.app;

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

