package com.dbgit.db;

public final class EnvReaders {
    private EnvReaders() {}

    public static int readPositiveInt(String key, int def) {
        String v = System.getenv(key);
        if (v == null || v.isBlank()) return def;
        try {
            int n = Integer.parseInt(v.trim());
            return n > 0 ? n : def;
        } catch (NumberFormatException e) {
            return def;
        }
    }

    public static double readNonNegativeDouble(String key, double def) {
        String v = System.getenv(key);
        if (v == null || v.isBlank()) return def;
        try {
            double d = Double.parseDouble(v.trim());
            return d >= 0 ? d : def;
        } catch (NumberFormatException e) {
            return def;
        }
    }
}

