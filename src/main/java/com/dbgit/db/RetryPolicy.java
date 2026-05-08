package com.dbgit.db;

public record RetryPolicy(int maxRetries, double delaySeconds) {
    public static RetryPolicy fromEnv() {
        int max = EnvReaders.readPositiveInt("DBGIT_DB_MAX_RETRIES", 3);
        double delay = EnvReaders.readNonNegativeDouble("DBGIT_DB_RETRY_DELAY_SEC", 1.0);
        return new RetryPolicy(max, delay);
    }
}

