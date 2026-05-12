# 아키텍처 (Java)

`dbgit`는 SQL Server 프로시저·함수 정의를 환경별로 조회해 해시 기반으로 SAME/DIFF를 판정합니다.

## 레이어

- `com.dbgit.cli`: CLI(옵션 파싱, 입력 검증, 출력 선택)
- `com.dbgit.factory`: 기본 의존성 조립(`CompositionRoot`)
- `com.dbgit.app`: 애플리케이션 오케스트레이션 + 훅 파이프라인 연동
- `com.dbgit.service`: 도메인 유스케이스(비교), 식별자 파싱
- `com.dbgit.db`: JDBC 연결/재시도, SQL 조회 레포지토리
- `com.dbgit.domain`: 도메인 모델(ProcDefinition 등)
- `com.dbgit.mapping`: DB 행 DTO 및 매퍼
- `com.dbgit.output`: 렌더러 플러그인/레지스트리
- `com.dbgit.hooks`: `Hook`, `HookEvent`, `HookPipeline`, `LoggingHook`
- `com.dbgit.validation`, `com.dbgit.errors`: 검증·오류 표준화

## 확장 포인트

- 렌더러: `RendererRegistry.register(new RendererImpl())`
- 훅: `new DbgitApp(service, new HookPipeline(List.of(new MyHook())))`
