package com.dbgit.cli;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class EnvListParserTest {
    @Test
    void parsesCommaSeparatedUppercase() {
        assertThat(EnvListParser.parse(" prd, stg,DEV ,, qa "))
                .containsExactly("PRD", "STG", "DEV", "QA");
    }
}

