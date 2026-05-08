package com.dbgit;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

public final class ProcCompare {

    private static final Pattern SPACE = Pattern.compile("\\s+");

    private static final String PROC_SQL = """
            SELECT TOP 1
                o.object_id,
                s.name AS schema_name,
                o.name,
                m.definition
            FROM sys.objects o
            JOIN sys.sql_modules m ON o.object_id = m.object_id
            JOIN sys.schemas s ON o.schema_id = s.schema_id
            WHERE o.type IN ('P', 'PC', 'FN', 'IF', 'TF')
              AND (
                    o.object_id = ?
                    OR o.name = ?
                    OR s.name + '.' + o.name = ?
              )
            ORDER BY
                CASE WHEN o.object_id = ? THEN 0 ELSE 1 END,
                o.name
            """;

    public record ProcDefinition(
            int objectId,
            String schemaName,
            String name,
            String definition,
            String normalizedDefinition
    ) {
        String fullName() {
            return schemaName + "." + name;
        }

        String digestHex() {
            try {
                MessageDigest md = MessageDigest.getInstance("SHA-256");
                byte[] h = md.digest(normalizedDefinition.getBytes(StandardCharsets.UTF_8));
                StringBuilder sb = new StringBuilder(h.length * 2);
                for (byte b : h) {
                    sb.append(String.format("%02x", b));
                }
                return sb.toString();
            } catch (NoSuchAlgorithmException e) {
                throw new IllegalStateException(e);
            }
        }
    }

    private static String normalize(String def) {
        return SPACE.matcher(def).replaceAll("");
    }

    private static Integer parseObjectId(String id) {
        try {
            return Integer.parseInt(id.trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static String jdbcUrl(EnvConfig c) {
        return String.format(
                "jdbc:sqlserver://%s:%d;databaseName=%s;encrypt=true;trustServerCertificate=true;loginTimeout=5",
                c.host(), c.port(), c.database());
    }

    private static Connection connectWithRetry(EnvConfig c) throws SQLException {
        int max = parseIntEnv("DBGIT_DB_MAX_RETRIES", 3);
        double delaySec = parseDoubleEnv("DBGIT_DB_RETRY_DELAY_SEC", 1.0);
        SQLException last = null;
        for (int attempt = 1; attempt <= max; attempt++) {
            try {
                Connection conn = DriverManager.getConnection(jdbcUrl(c), c.user(), c.password());
                return conn;
            } catch (SQLException ex) {
                last = ex;
                System.err.printf("DB 연결 실패 env=%s 시도 %d/%d: %s%n", c.name(), attempt, max, ex.getMessage());
                if (attempt < max && delaySec > 0) {
                    try {
                        Thread.sleep((long) (delaySec * 1000));
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new SQLException("interrupted", ie);
                    }
                }
            }
        }
        throw last != null ? last : new SQLException("연결 실패");
    }

    private static int parseIntEnv(String k, int def) {
        String v = System.getenv(k);
        if (v == null || v.isBlank()) return def;
        try {
            int n = Integer.parseInt(v.trim());
            return n > 0 ? n : def;
        } catch (NumberFormatException e) {
            return def;
        }
    }

    private static double parseDoubleEnv(String k, double def) {
        String v = System.getenv(k);
        if (v == null || v.isBlank()) return def;
        try {
            double d = Double.parseDouble(v.trim());
            return d >= 0 ? d : def;
        } catch (NumberFormatException e) {
            return def;
        }
    }

    public static ProcDefinition fetch(EnvConfig cfg, String procIdentifier) throws SQLException {
        Integer oid = parseObjectId(procIdentifier);
        try (Connection conn = connectWithRetry(cfg);
             PreparedStatement ps = conn.prepareStatement(PROC_SQL)) {
            if (oid != null) {
                ps.setInt(1, oid);
                ps.setInt(4, oid);
            } else {
                ps.setObject(1, null, java.sql.Types.INTEGER);
                ps.setObject(4, null, java.sql.Types.INTEGER);
            }
            ps.setString(2, procIdentifier);
            ps.setString(3, procIdentifier);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    throw new IllegalArgumentException(cfg.name() + "에서 프로시저를 찾지 못했습니다: " + procIdentifier);
                }
                int objectId = rs.getInt(1);
                String sn = rs.getString(2);
                String name = rs.getString(3);
                String def = rs.getString(4);
                if (def == null) def = "";
                return new ProcDefinition(objectId, sn, name, def, normalize(def));
            }
        }
    }

    public static Map<String, ProcDefinition> compareAll(List<EnvConfig> cfgs, String procId)
            throws SQLException {
        Map<String, ProcDefinition> out = new LinkedHashMap<>();
        for (EnvConfig c : cfgs) {
            out.put(c.name(), fetch(c, procId));
        }
        return out;
    }
}
