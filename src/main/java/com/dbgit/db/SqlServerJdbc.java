package com.dbgit.db;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

import com.dbgit.config.EnvConfig;

public final class SqlServerJdbc {
    private SqlServerJdbc() {}

    public static String jdbcUrl(EnvConfig c) {
        return String.format(
                "jdbc:sqlserver://%s:%d;databaseName=%s;encrypt=true;trustServerCertificate=true;loginTimeout=5",
                c.host(), c.port(), c.database()
        );
    }

    public static Connection connect(EnvConfig c) throws SQLException {
        return DriverManager.getConnection(jdbcUrl(c), c.user(), c.password());
    }
}

