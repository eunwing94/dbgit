package com.dbgit.domain;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Objects;

public record ProcDefinition(
        int objectId,
        String schemaName,
        String name,
        String definition,
        String normalizedDefinition
) {
    public ProcDefinition {
        schemaName = Objects.requireNonNull(schemaName, "schemaName");
        name = Objects.requireNonNull(name, "name");
        definition = definition == null ? "" : definition;
        normalizedDefinition = Objects.requireNonNull(normalizedDefinition, "normalizedDefinition");
    }

    public String fullName() {
        return schemaName + "." + name;
    }

    public String digestHex() {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] h = md.digest(normalizedDefinition.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(h.length * 2);
            for (byte b : h) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}

