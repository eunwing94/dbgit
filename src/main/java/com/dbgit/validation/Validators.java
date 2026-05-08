package com.dbgit.validation;

import java.util.List;

import com.dbgit.error.DbgitException;
import com.dbgit.error.ErrorCode;

public final class Validators {
    private Validators() {}

    public static void requireNonBlank(String v, String label) {
        if (v == null || v.isBlank()) {
            throw new DbgitException(ErrorCode.INVALID_ARGUMENT, label + " 값이 비어있습니다.");
        }
    }

    public static void requireContains(List<String> envs, String baseline) {
        if (envs == null || !envs.contains(baseline)) {
            throw new DbgitException(ErrorCode.INVALID_ARGUMENT, "baseline 환경이 envs 목록에 포함되어야 합니다.");
        }
    }
}

