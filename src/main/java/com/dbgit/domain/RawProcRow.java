package com.dbgit.domain;

public record RawProcRow(
        int objectId,
        String schemaName,
        String name,
        String definition
) {
}

