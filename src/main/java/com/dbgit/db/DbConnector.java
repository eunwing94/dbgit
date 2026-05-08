package com.dbgit.db;

import java.sql.Connection;
import java.sql.SQLException;

import com.dbgit.config.EnvConfig;

public interface DbConnector {
    Connection connect(EnvConfig cfg) throws SQLException;
}

