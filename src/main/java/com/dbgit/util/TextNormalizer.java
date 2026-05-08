package com.dbgit.util;

import java.util.regex.Pattern;

public final class TextNormalizer {
    private static final Pattern SPACE = Pattern.compile("\\s+");

    private TextNormalizer() {}

    public static String normalizeSqlModuleBody(String def) {
        if (def == null) return "";
        return SPACE.matcher(def).replaceAll("");
    }
}

