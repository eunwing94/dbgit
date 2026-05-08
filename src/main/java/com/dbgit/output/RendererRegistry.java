package com.dbgit.output;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

public final class RendererRegistry {

    private final Map<OutputFormat, Renderer> renderers = new LinkedHashMap<>();

    public RendererRegistry register(Renderer r) {
        Objects.requireNonNull(r, "renderer");
        renderers.put(r.format(), r);
        return this;
    }

    public Renderer get(OutputFormat f) {
        Renderer r = renderers.get(f);
        if (r == null) throw new IllegalStateException("등록되지 않은 렌더러: " + f);
        return r;
    }
}

