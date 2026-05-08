package com.dbgit.error;

public class DbgitException extends RuntimeException {
    private final ErrorCode code;

    public DbgitException(ErrorCode code, String message) {
        super(message);
        this.code = code;
    }

    public DbgitException(ErrorCode code, String message, Throwable cause) {
        super(message, cause);
        this.code = code;
    }

    public ErrorCode code() {
        return code;
    }
}

