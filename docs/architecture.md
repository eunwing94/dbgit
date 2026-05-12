# 아키텍처 (C#)

C# 구현(`feature/csharp01`)은 `Microsoft.Data.SqlClient`로 SQL Server를 조회하고,
정의 텍스트를 정규화/해시하여 SAME/DIFF를 판단합니다.

## 계층 구성

- `Program.cs`: CLI 파싱, 검증, DI 조립(팩토리), 실행
- `Config/`: `EnvConfig`, `ConfigLoader` — `.env`/환경 변수 로딩
- `Db/`: `ISqlConnectionFactory`, `SqlConnectionFactory`, `IProcDefinitionRepository`, `SqlProcDefinitionRepository` — 연결·조회
- `Domain/`: `ProcDefinition` — 도메인 모델 및 digest
- `Mapping/`: `ProcDefinitionRowDto`, `ProcDefinitionMapper` — DB 행 → 도메인
- `Service/`: `ProcCompareService` — 환경 간 비교 유스케이스
- `Render/`: `IRenderer`, `RendererRegistry`, `RendererRegistryFactory`, `TextRenderer`/`JsonRenderer`/`MarkdownRenderer`
- `Validation/`: `CliOptions`, `CliOptionsValidator` — CLI 입력 스키마 검증
- `Errors/`: `ErrorCode`, `DbgitException`, `ExceptionMapper` — 오류 표준화
- `Hooks/`: `IHook`, `LoggingHook`, `HookPipeline`, `HookEvent` — 전/후 이벤트 미들웨어
- `Cli/`: `EnvList` — 환경 목록 파싱

## 확장 포인트

- 저장소: `IProcDefinitionRepository` 구현체 추가 후 `ProcCompareService`에 주입
- 출력: `IRenderer` 구현 후 `RendererRegistryFactory.CreateDefault()`에 등록
- 훅: `HookPipeline`에 `IHook` 구현체 추가
