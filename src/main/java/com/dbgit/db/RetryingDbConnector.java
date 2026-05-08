package com.dbgit.db;

import java.sql.Connection;
import java.sql.SQLException;

import com.dbgit.config.EnvConfig;

public final class RetryingDbConnector implements DbConnector {

    private final DbConnector delegate;
    private final RetryPolicy policy;

    public RetryingDbConnector(DbConnector delegate, RetryPolicy policy) {
        this.delegate = delegate;
        this.policy = policy;
    }

    @Override
    public Connection connect(EnvConfig cfg) throws SQLException {
        SQLException last = null;
        for (int attempt = 1; attempt <= policy.maxRetries(); attempt++) {
            try {
                return delegate.connect(cfg);
            } catch (SQLException ex) {
                last = ex;
                System.err.printf("DB 연결 실패 env=%s 시도 %d/%d: %s%n",
                        cfg.name(), attempt, policy.maxRetries(), ex.getMessage());
                if (attempt < policy.maxRetries() && policy.delaySeconds() > 0) {
                    try {
                        Thread.sleep((long) (policy.delaySeconds() * 1000));
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new SQLException("interrupted", ie);
                    }
                }
            }
        }
        throw last != null ? last : new SQLException("연결 실패");
    }
}

