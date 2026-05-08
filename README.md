# dbgit — Rust (`feature/rust01`)

SQL Server **프로시저·함수** 정의를 환경별로 비교하는 CLI (`tiberius` + Tokio).

## 요구 사항

- Rust toolchain (stable)
- `.env`에 `<ENV>_HOST`, `<ENV>_PORT`, `<ENV>_USER`, `<ENV>_PASSWORD`, `<ENV>_DATABASE`

## 실행

```bash
cargo run -- dbo.usp_Sample --envs PRD,STG,DEV,QA --baseline PRD --output json
```

## 빌드

```bash
cargo build --release
```

## 출력

`--output text` · `json` · `markdown`

## 재시도

- `DBGIT_DB_MAX_RETRIES` (기본 3)
- `DBGIT_DB_RETRY_DELAY_SEC` (기본 1.0)
