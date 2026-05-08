package com.dbgit.service;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

/**
 * 통합 테스트 스켈레톤.
 * - 로컬/사내 네트워크 SQL Server가 필요하므로 기본적으로 비활성화
 * - 필요 시 @Disabled 제거 후 환경변수/ .env를 구성해 실행
 */
@Disabled("requires live SQL Server")
class ProcCompareServiceIT {
    @Test
    void comparesLiveServer() {
        assertThat(true).isTrue();
    }
}

