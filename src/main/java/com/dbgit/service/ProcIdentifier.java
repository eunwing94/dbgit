package com.dbgit.service;

public record ProcIdentifier(Integer objectId, String raw) {
    public static ProcIdentifier parse(String s) {
        if (s == null) return new ProcIdentifier(null, "");
        String t = s.trim();
        try {
            return new ProcIdentifier(Integer.parseInt(t), t);
        } catch (NumberFormatException e) {
            return new ProcIdentifier(null, t);
        }
    }
}

