package com.dbgit.db;

import java.sql.Connection;
import java.sql.SQLException;

import com.dbgit.config.EnvConfig;

public final class SqlServerConnector implements DbConnector {
    @Override
    public Connection connect(EnvConfig cfg) throws SQLException {
        return SqlServerJdbc.connect(cfg);
    }
}

