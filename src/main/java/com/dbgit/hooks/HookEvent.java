package com.dbgit.hooks;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import com.dbgit.config.EnvConfig;
import com.dbgit.domain.ProcDefinition;

public final class HookEvent {

    public enum Type {
        BEFORE_COMPARE,
        AFTER_COMPARE
    }

    private final Type type;
    private final Instant at;
    private final List<EnvConfig> environments;
    private final String procIdentifier;
    private final Map<String, ProcDefinition> result;

    private HookEvent(Type type, List<EnvConfig> environments, String procIdentifier, Map<String, ProcDefinition> result) {
        this.type = Objects.requireNonNull(type, "type");
        this.at = Instant.now();
        this.environments = List.copyOf(environments == null ? List.of() : environments);
        this.procIdentifier = Objects.requireNonNull(procIdentifier, "procIdentifier");
        this.result = result;
    }

    public static HookEvent beforeCompare(List<EnvConfig> envs, String procIdentifier) {
        return new HookEvent(Type.BEFORE_COMPARE, envs, procIdentifier, null);
    }

    public static HookEvent afterCompare(List<EnvConfig> envs, String procIdentifier, Map<String, ProcDefinition> result) {
        return new HookEvent(Type.AFTER_COMPARE, envs, procIdentifier, Map.copyOf(result));
    }

    public Type type() {
        return type;
    }

    public Instant at() {
        return at;
    }

    public List<EnvConfig> environments() {
        return environments;
    }

    public String procIdentifier() {
        return procIdentifier;
    }

    public Map<String, ProcDefinition> result() {
        return result;
    }
}

