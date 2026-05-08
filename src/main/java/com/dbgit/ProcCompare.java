package com.dbgit;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ProcCompare {

    public record ProcDefinition(
            int objectId,
            String schemaName,
            String name,
            String definition,
            String normalizedDefinition
    ) {
        String fullName() {
            return schemaName + "." + name;
        }

        String digestHex() {
            return new com.dbgit.domain.ProcDefinition(
                    objectId, schemaName, name, definition, normalizedDefinition
            ).digestHex();
        }
    }

    public static Map<String, ProcDefinition> compareAll(List<EnvConfig> cfgs, String procId)
            throws java.sql.SQLException {
        Map<String, ProcDefinition> out = new LinkedHashMap<>();
        var connector = new com.dbgit.db.RetryingDbConnector(
                new com.dbgit.db.SqlServerConnector(),
                com.dbgit.db.RetryPolicy.fromEnv()
        );
        var service = new com.dbgit.service.ProcCompareService(connector, new com.dbgit.db.ProcSqlRepository());
        for (EnvConfig c : cfgs) {
            com.dbgit.config.EnvConfig cc = new com.dbgit.config.EnvConfig(
                    c.name(), c.host(), c.port(), c.user(), c.password(), c.database()
            );
            var def = service.compareAll(List.of(cc), procId).get(cc.name());
            out.put(c.name(), new ProcDefinition(
                    def.objectId(),
                    def.schemaName(),
                    def.name(),
                    def.definition(),
                    def.normalizedDefinition()
            ));
        }
        return out;
    }
}
