package com.dbgit;

import java.util.Locale;
import java.util.Objects;

import io.github.cdimascio.dotenv.Dotenv;

public record EnvConfig(
        String name,
        String host,
        int port,
        String user,
        String password,
        String database
) {
    public static EnvConfig load(Dotenv dotenv, String envName) {
        String prefix = envName.toUpperCase(Locale.ROOT);
        String host = require(dotenv, prefix + "_HOST", envName);
        String portRaw = require(dotenv, prefix + "_PORT", envName);
        int port;
        try {
            port = Integer.parseInt(portRaw.trim());
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException(envName + " PORT 형식 오류: " + portRaw);
        }
        String user = require(dotenv, prefix + "_USER", envName);
        String password = require(dotenv, prefix + "_PASSWORD", envName);
        String database = require(dotenv, prefix + "_DATABASE", envName);
        return new EnvConfig(prefix, host, port, user, password, database);
    }

    private static String require(Dotenv dotenv, String key, String envLabel) {
        String v = firstNonBlank(dotenv.get(key), System.getenv(key));
        if (v == null || v.isBlank()) {
            throw new IllegalArgumentException(envLabel + " 설정 누락: " + key);
        }
        return v;
    }

    private static String firstNonBlank(String a, String b) {
        if (a != null && !a.isBlank()) return a;
        return Objects.requireNonNullElse(b, "");
    }
}
