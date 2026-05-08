package com.dbgit;

/**
 * 레거시 비교 API.
 *
 * 새 구조에서는 `com.dbgit.service.ProcCompareService` 사용을 권장합니다.
 * (기존 호출부 호환을 위해 얇은 어댑터 형태로 유지)
 */
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
