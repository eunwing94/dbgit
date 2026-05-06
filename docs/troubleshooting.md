# 트러블슈팅

## pyodbc / ODBC

### `Can't open lib 'ODBC Driver 18 for SQL Server'`

- macOS: [Microsoft ODBC Driver 18](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-macos) 및 **unixODBC** 설치 후 재실행.
- 터미널에서 드라이버 이름 확인: `odbcinst -q -d`

### `Library not loaded: ... libodbc.2.dylib`

- Homebrew로 `unixodbc` 설치: `brew install unixodbc`
- 권한 오류 시 Homebrew 디렉터리 소유권 정리 후 재설치.

### Docker 이미지 빌드 실패 (ARM Mac 등)

- `Dockerfile`은 **amd64**용 Microsoft 패키지 저장소를 사용합니다. ARM에서는 빌드 대신 로컬 실행을 사용하거나, 멀티 스테이지·별도 Dockerfile을 검토하세요.

## 연결·방화벽

- DB가 사내 IP(`10.x` 등)만 허용하면, **클라우드(Streamlit Cloud 등)** 에서는 연결되지 않습니다. VPN 또는 허용 IP 설정이 필요합니다.

## 환경 변수

| 변수 | 설명 |
|:-----|:-----|
| `DBGIT_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `OFF` 등 |
| `DBGIT_LOG` | `1` 이면 레벨 미지정 시 INFO에 가깝게 동작 |
| `DBGIT_DB_MAX_RETRIES` | DB 연결 재시도 횟수 (기본 3) |
| `DBGIT_DB_RETRY_DELAY_SEC` | 재시도 간 대기 초 (기본 1.0) |

## Streamlit

- 포트 충돌 시 터미널에 표시된 다른 포트로 접속하세요.
- `dotenv 경로`가 잘못되면 `.env`가 로드되지 않습니다.
