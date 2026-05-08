package com.dbgit.service;

/**
 * 비교 유스케이스(서비스).
 *
 * 각 환경에 대해 SQL Server에서 프로시저/함수 정의를 조회하고,
 * 정규화된 정의를 포함한 도메인 모델을 생성합니다.
 */
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import com.dbgit.config.EnvConfig;
import com.dbgit.db.DbConnector;
import com.dbgit.db.ProcSqlRepository;
import com.dbgit.domain.ProcDefinition;
import com.dbgit.domain.RawProcRow;
import com.dbgit.util.TextNormalizer;

public final class ProcCompareService {

    private final DbConnector connector;
    private final ProcSqlRepository repo;

    public ProcCompareService(DbConnector connector, ProcSqlRepository repo) {
        this.connector = Objects.requireNonNull(connector, "connector");
        this.repo = Objects.requireNonNull(repo, "repo");
    }

    public Map<String, ProcDefinition> compareAll(List<EnvConfig> envs, String procIdentifier) {
        Map<String, ProcDefinition> out = new LinkedHashMap<>();
        ProcIdentifier id = ProcIdentifier.parse(procIdentifier);
        for (EnvConfig e : envs) {
            out.put(e.name(), fetchOne(e, id));
        }
        return out;
    }

    private ProcDefinition fetchOne(EnvConfig env, ProcIdentifier id) {
        try (var conn = connector.connect(env)) {
            RawProcRow row = repo.fetchOne(conn, id.objectId(), id.raw());
            if (row == null) {
                throw new IllegalArgumentException(env.name() + "에서 프로시저를 찾지 못했습니다: " + id.raw());
            }
            String def = row.definition() == null ? "" : row.definition();
            return new ProcDefinition(
                    row.objectId(),
                    row.schemaName(),
                    row.name(),
                    def,
                    TextNormalizer.normalizeSqlModuleBody(def)
            );
        } catch (Exception ex) {
            if (ex instanceof RuntimeException re) throw re;
            throw new RuntimeException(ex);
        }
    }
}

