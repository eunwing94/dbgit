# 아키텍처 (TypeScript)

TypeScript 구현(`feature/typescript01`)은 `mssql` 드라이버로 `sys.sql_modules`를 조회해
정의 텍스트를 정규화/해시하여 SAME/DIFF를 판정합니다.

## 구성

- `src/cli.ts`: CLI 진입 및 옵션 파싱
- `src/config.ts`: 환경별 접속 정보 로딩
- `src/db.ts`: SQL Server 질의
- `src/compare.ts`: 조회/정규화/해시 비교
- `src/outputFormat.ts`: text/json/markdown 출력

## 확장 포인트(스켈레톤)

- `src/hooks/*`: before/after compare 훅
- `src/render/*`: RendererRegistry (출력 플러그인)

# 아키텍처 (Rust)

Rust 구현(`feature/rust01`)은 SQL Server의 `sys.sql_modules`를 조회해 정의를 얻고,
정의 텍스트를 정규화한 뒤 digest(SHA-256)로 SAME/DIFF를 판단합니다.

## 모듈

- `main.rs`: CLI 진입, 옵션 파싱, 출력 선택
- `config.rs`: `.env`/환경변수로 환경 설정 로딩
- `compare.rs`: 조회/정규화/해시 및 비교
- `output.rs`: text/json/markdown 렌더링

## 확장 포인트(스켈레톤)

- `cli.rs`: 입력 검증/파싱 분리
- `hooks.rs`: 비교 전/후 이벤트 훅
- `render.rs`: 포맷 렌더러 레지스트리(플러그인)

