package com.dbgit.output;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.LinkedHashMap;

import org.junit.jupiter.api.Test;

import com.dbgit.domain.ProcDefinition;

class TextRendererTest {
    @Test
    void rendersBaselineAndDiff() {
        ProcDefinition prd = new ProcDefinition(1, "dbo", "p", "A", "A");
        ProcDefinition stg = new ProcDefinition(1, "dbo", "p", "B", "B");
        var defs = new LinkedHashMap<String, ProcDefinition>();
        defs.put("PRD", prd);
        defs.put("STG", stg);

        String out = new TextRenderer().render("PRD", defs);
        assertThat(out).contains("기준 환경: PRD");
        assertThat(out).contains("PRD: SAME");
        assertThat(out).contains("STG: DIFF");
    }
}

