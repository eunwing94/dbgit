package com.dbgit.output;

import java.util.Map;

import com.dbgit.domain.ProcDefinition;

public interface Renderer {
    OutputFormat format();

    String render(String baselineEnvName, Map<String, ProcDefinition> defs);
}

