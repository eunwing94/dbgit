package com.dbgit.output;

public enum OutputFormat {
    TEXT("text"),
    JSON("json"),
    MARKDOWN("markdown");

    private final String id;

    OutputFormat(String id) {
        this.id = id;
    }

    public String id() {
        return id;
    }

    public static OutputFormat parse(String raw) {
        String v = raw == null ? "" : raw.trim().toLowerCase();
        for (OutputFormat f : values()) {
            if (f.id.equals(v)) return f;
        }
        throw new IllegalArgumentException("output은 text, json, markdown 중 하나여야 합니다.");
    }
}

