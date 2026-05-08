# 설정(.env / 환경변수)

## .env 키 규칙

환경 이름이 `PRD`, `STG` 라면 다음 키를 사용합니다.

- `PRD_HOST`, `PRD_PORT`, `PRD_USER`, `PRD_PASSWORD`, `PRD_DATABASE`
- `STG_HOST`, `STG_PORT`, `STG_USER`, `STG_PASSWORD`, `STG_DATABASE`

값이 `.env`에 없으면 같은 이름의 OS 환경 변수를 확인합니다.

## DB 연결 재시도

- `DBGIT_DB_MAX_RETRIES` (기본 3)
- `DBGIT_DB_RETRY_DELAY_SEC` (기본 1.0)

