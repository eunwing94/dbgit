# 아키텍처 (TypeScript)

TypeScript 구현(`feature/typescript01`)은 `mssql` 드라이버로 `sys.sql_modules`를 조회해
정의 텍스트를 정규화/해시하여 SAME/DIFF를 판정합니다.

## 구성

- `src/cli.ts`: CLI 진입 및 옵션 파싱
- `src/factory.ts`: 기본 훅 파이프라인 조립
- `src/config.ts`: 환경별 접속 정보 로딩
- `src/db.ts`: SQL Server 질의
- `src/compare.ts`: 조회/정규화/해시 비교
- `src/outputFormat.ts`: text/json/markdown 출력
- `src/hooks/*`: 이벤트 타입, `Hook`, `LoggingHook`, `HookPipeline`

## 확장 포인트

- `src/render/*`: RendererRegistry (출력 플러그인)
- 훅: `createDefaultHookPipeline()` 대신 커스텀 `HookPipeline` 구성
