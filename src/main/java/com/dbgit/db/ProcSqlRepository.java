package com.dbgit.db;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import com.dbgit.domain.RawProcRow;

public final class ProcSqlRepository {

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

    public RawProcRow fetchOne(Connection conn, Integer objectId, String identifier) throws SQLException {
        try (PreparedStatement ps = conn.prepareStatement(PROC_SQL)) {
            if (objectId != null) {
                ps.setInt(1, objectId);
                ps.setInt(4, objectId);
            } else {
                ps.setObject(1, null, java.sql.Types.INTEGER);
                ps.setObject(4, null, java.sql.Types.INTEGER);
            }
            ps.setString(2, identifier);
            ps.setString(3, identifier);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) return null;
                return new RawProcRow(
                        rs.getInt(1),
                        rs.getString(2),
                        rs.getString(3),
                        rs.getString(4)
                );
            }
        }
    }
}

