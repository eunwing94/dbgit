package com.dbgit.cli;

import java.util.Arrays;
import java.util.List;

public final class EnvListParser {
    private EnvListParser() {}

    public static List<String> parse(String raw) {
        String v = raw == null ? "" : raw;
        return Arrays.stream(v.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(s -> s.toUpperCase())
                .toList();
    }
}

