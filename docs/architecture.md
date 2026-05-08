# 아키텍처 (Go)

Go 구현(`feature/go01`)은 SQL Server의 `sys.sql_modules`를 조회해 프로시저/함수 정의를 얻고,
정의 텍스트를 정규화한 뒤 SHA-256 digest로 SAME/DIFF를 판단합니다.

## 디렉터리

- `cmd/dbgit`: 실행 진입점(플래그 파싱, 출력 선택)
- `internal/config`: `.env`/환경변수 기반 환경 설정 로딩
- `internal/db`: SQL Server 조회 및 재시도/타임아웃
- `internal/compare`: 비교 유스케이스(환경별 조회/정규화/해시)
- `internal/output`: text/json/markdown 출력 포맷

## 확장 포인트(스켈레톤)

- `internal/hooks`: 비교 전/후 이벤트 훅
- `internal/output/renderer`: 렌더러 레지스트리로 포맷 확장

