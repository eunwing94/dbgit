# dbgit — TypeScript (`feature/typescript01`)

이 브랜치는 **Node.js 18+ / TypeScript** 로 작성된 **CLI 전용** 구현입니다. (Python·Streamlit 버전은 `main` / `feature/eun-0506` 참고.)

## 요구 사항

- Node.js 18+
- SQL Server 네트워크 접근 가능한 환경
- `.env`에 `PRD_HOST`, `PRD_PORT`, `PRD_USER`, `PRD_PASSWORD`, `PRD_DATABASE` 등 (환경 접두어 규칙은 기존과 동일)

## 설치·빌드

```bash
npm install
npm run build
```

## CLI

```bash
node dist/cli.js dbo.usp_Sample --baseline PRD --envs PRD,STG,DEV,QA
node dist/cli.js dbo.usp_Sample --output json
```

환경 변수 파일:

```bash
node dist/cli.js dbo.usp_Sample --dotenv .env
```

## Docker

```bash
docker compose run --rm dbgit node dist/cli.js --help
```

`.env`는 `docker-compose.yml`에서 마운트됩니다.

## 프로젝트 구조

| 경로 | 역할 |
|:-----|:-----|
| `src/config.ts` | `EnvConfig`, 환경변수 로드 |
| `src/db.ts` | `mssql` 연결·재시도 |
| `src/compare.ts` | `sys.sql_modules` 조회·정규화·digest |
| `src/outputFormat.ts` | text / json / markdown |
| `src/cli.ts` | Commander CLI |

## 다른 언어 브랜치

- `feature/csharp01` — .NET  
- `feature/go01` — Go  
- `feature/rust01` — Rust  
- `feature/java01` — Java  
