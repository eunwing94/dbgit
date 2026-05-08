package com.dbgit.util;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class TextNormalizerTest {
    @Test
    void removesAllWhitespace() {
        String in = "CREATE  PROC  dbo.usp\nAS\r\nBEGIN  SELECT 1 \t END";
        assertThat(TextNormalizer.normalizeSqlModuleBody(in))
                .isEqualTo("CREATEPROCdbo.uspASBEGINSELECT1END");
    }
}

