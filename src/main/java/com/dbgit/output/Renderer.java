package com.dbgit.output;

/**
 * 출력 렌더러 플러그인 인터페이스.
 *
 * `RendererRegistry`에 등록하여 포맷(text/json/markdown 등)을 확장할 수 있습니다.
 */
import java.util.Map;

import com.dbgit.domain.ProcDefinition;

public interface Renderer {
    OutputFormat format();

    String render(String baselineEnvName, Map<String, ProcDefinition> defs);
}

