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

