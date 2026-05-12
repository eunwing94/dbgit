# 아키텍처 (Python / Streamlit)

`feature/eun-0506` 브랜치의 Python 패키지(`src/dbgit`)는 SQL Server `sys.sql_modules` 기반으로
프로시저·함수 정의를 조회하고, 정규화·해시로 환경 간 SAME/DIFF를 판단합니다.

## 구성

- `src/dbgit/cli.py`: CLI 진입, 옵션 파싱, 출력
- `src/dbgit/factory.py`: 기본 훅 파이프라인 조립
- `src/dbgit/config.py`, `src/dbgit/db.py`: 접속·질의
- `src/dbgit/compare.py`: 조회·정규화·비교
- `src/dbgit/output_format.py`: text/json/markdown
- `src/dbgit/st_app.py`, `src/dbgit/ui/*`: Streamlit UI
- `src/dbgit/hooks/*`: `HookContext`, `HookEventType`, `LoggingHook`, `HookPipeline`

## 확장 포인트

- CLI에서 `create_default_hook_pipeline()` 대신 커스텀 `HookPipeline`을 주입해 전처리·메트릭 등을 붙일 수 있습니다.
