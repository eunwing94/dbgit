# dbgit — Go (`feature/go01`)

SQL Server **프로시저·함수** 정의를 환경별로 조회해 해시(digest)로 비교하는 **CLI** 구현입니다.

## 요구 사항

- Go 1.22+
- `.env`: `<ENV>_HOST`, `<ENV>_PORT`, `<ENV>_USER`, `<ENV>_PASSWORD`, `<ENV>_DATABASE`  
  (예시: `.env.example`)

## 실행

```bash
go run ./cmd/dbgit -- dbo.usp_Sample --envs PRD,STG,DEV,QA --baseline PRD --output json
```

## 빌드

```bash
go build -o dbgit ./cmd/dbgit
```

## 출력

- `--output text` (기본)
- `--output json`
- `--output markdown`

## 재시도

- `DBGIT_DB_MAX_RETRIES` (기본 3)
- `DBGIT_DB_RETRY_DELAY_SEC` (기본 1.0)

## 다른 언어 브랜치

- `feature/typescript01`, `feature/csharp01` 등
