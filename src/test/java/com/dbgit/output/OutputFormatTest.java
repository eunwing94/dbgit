package com.dbgit.output;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class OutputFormatTest {
    @Test
    void parsesKnownFormats() {
        assertThat(OutputFormat.parse("text")).isEqualTo(OutputFormat.TEXT);
        assertThat(OutputFormat.parse(" JSON ")).isEqualTo(OutputFormat.JSON);
        assertThat(OutputFormat.parse("Markdown")).isEqualTo(OutputFormat.MARKDOWN);
    }

    @Test
    void rejectsUnknownFormat() {
        assertThatThrownBy(() -> OutputFormat.parse("xml"))
                .isInstanceOf(IllegalArgumentException.class);
    }
}

