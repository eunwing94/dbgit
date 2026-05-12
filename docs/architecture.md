# 아키텍처 (Go)

Go 구현(`feature/go01`)은 SQL Server의 `sys.sql_modules`를 조회해 프로시저/함수 정의를 얻고,
정의 텍스트를 정규화한 뒤 SHA-256 digest로 SAME/DIFF를 판단합니다.

## 계층 구성

- `cmd/dbgit`: CLI 플래그 파싱, 조립, 실행
- `internal/config`: `.env`/환경변수 기반 `EnvConfig` 로딩
- `internal/db`: 연결 문자열·재시도·`OpenWithRetry`
- `internal/domain`: `ProcDefinition` 도메인 모델
- `internal/repository`: `ProcDefinitionRepository` 인터페이스 및 `SQLProcRepository` 구현
- `internal/service`: `CompareService` 비교 유스케이스
- `internal/render`: `Renderer` 인터페이스, `Registry`, `ParseKind`, text/json/markdown 구현체
- `internal/errors`: `Code`, `Error` 표준 오류
- `internal/hooks`: `Hook` 인터페이스, `Event`, `Pipeline`, `LoggingHook`
- `internal/cli`: 환경 목록 파싱

## 확장 포인트

- 저장소: `ProcDefinitionRepository` 구현체를 `CompareService`에 주입
- 출력: `Renderer` 구현 후 `Registry.Register`로 등록
- 훅: `hooks.NewPipeline`에 커스텀 `Hook` 추가
