# dbgit (Java)

**SQL Server** 프로시저·함수 정의를 여러 환경(PR · STG · DEV · QA 등)에서 비교하는 CLI입니다.

## 요구 사항

- JDK 17+
- Apache Maven 3.9+
- 접속 대상이 Microsoft SQL Server이며, JDBC URL에 `encrypt=true;trustServerCertificate=true`를 사용합니다.

## 빌드

```bash
mvn -q package
```

실행 가능한 fat JAR: `target/dbgit.jar`

```bash
java -jar target/dbgit.jar --help
```

## 환경 변수

프로젝트 루트에 `.env`를 두고, 환경 이름 접두어 규칙은 다음과 같습니다.

- `{ENV}_HOST`, `{ENV}_PORT`, `{ENV}_USER`, `{ENV}_PASSWORD`, `{ENV}_DATABASE`

`--dotenv`로 다른 파일 경로를 지정할 수 있습니다. 값이 비어 있으면 동일한 이름의 OS 환경 변수를 참조합니다.

## 사용 예

```bash
java -jar target/dbgit.jar dbo.usp_Sample --baseline PRD --envs PRD,STG,DEV,QA
```

```bash
java -jar target/dbgit.jar 123456 --output json
java -jar target/dbgit.jar dbo.usp_Sample --output markdown
```

### 재시도

DB 연결 실패 시 재시도 횟수·간격은 환경 변수로 조절합니다.

- `DBGIT_DB_MAX_RETRIES` (기본 3)
- `DBGIT_DB_RETRY_DELAY_SEC` (기본 1.0)

## 보안

DB 비밀번호·계정은 Git에 커밋하지 마세요. `.env`는 `.gitignore`에 포함되어 있습니다.

## 기여

[CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.
