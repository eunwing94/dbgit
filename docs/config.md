# 설정(.env / 환경변수)

## .env 키 규칙

환경 이름이 `PRD`, `STG` 라면 다음 키를 사용합니다.

- `PRD_HOST`, `PRD_PORT`, `PRD_USER`, `PRD_PASSWORD`, `PRD_DATABASE`
- `STG_HOST`, `STG_PORT`, `STG_USER`, `STG_PASSWORD`, `STG_DATABASE`

`.env`가 없거나 키가 없으면 OS 환경 변수를 사용합니다.

# 설정(.env / 환경변수)

## .env 키 규칙

환경 이름이 `PRD`, `STG` 라면 다음 키를 사용합니다.

- `PRD_HOST`, `PRD_PORT`, `PRD_USER`, `PRD_PASSWORD`, `PRD_DATABASE`
- `STG_HOST`, `STG_PORT`, `STG_USER`, `STG_PASSWORD`, `STG_DATABASE`

`.env`를 쓰지 않으면 같은 이름의 OS 환경 변수를 사용합니다.

