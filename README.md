# DB 형상 비교

프로시저·함수·뷰·사용자 테이블(컬럼 스키마)을 환경별로 비교하고, 공통코드(`CM_CD_D`) 갭도 비교할 수 있습니다.

## GitHub Pages

정적 랜딩 페이지: [https://eunwing94.github.io/dbgit/](https://eunwing94.github.io/dbgit/)  
(저장소 루트 또는 `docs/`에 `index.html`이 있어야 합니다. Settings → Pages에서 **main** + **/(root)** 또는 **/docs** 중 배포 경로와 맞추세요.)

## 실행 방법 (요약)

1. 리포지토리 루트에서 가상환경 생성 및 활성화
2. `pip install -r requirements.txt`
3. `.env`에 DB 접속 정보 설정 (`PRD_HOST`, `PRD_PORT`, … `*_DATABASE` 등)
4. UI: `streamlit run app.py` 후 브라우저에서 접속 (기본 `http://localhost:8501`, 포트는 실행 시 출력 참고)
5. CLI: 아래 “CLI 사용법” 참고 (`PYTHONPATH` 필요)

## 준비

1. 파이썬 가상환경 준비 (예: `python -m venv .venv` 후 활성화)
2. 의존성 설치

```
pip install -r requirements.txt
```

3. SQL Server ODBC 드라이버 설치

- macOS: **Microsoft ODBC Driver 18 for SQL Server**, **unixODBC** 필요

4. `.env` 설정

```
cp .env.example .env
```

`.env` 안에 각 환경의 접속정보를 채워주세요. (예: `PRD_HOST`, `PRD_PORT`, `PRD_USER`, `PRD_PASSWORD`, `PRD_DATABASE=ERP`)

## UI 실행 (Streamlit)

프로젝트 루트에서:

```
streamlit run app.py
```

터미널에 표시되는 **Local URL**로 접속합니다. (포트는 환경마다 다를 수 있음)

### 화면에서 할 수 있는 것

- **객체 검색**: 기준 환경 DB에서 이름·본문(정의)으로 검색 → 결과 엑셀 다운로드 → 선택 시 **단일 비교** 탭 입력란에 반영
- **단일 비교**: 유형(프로시저·함수 / 뷰 / 테이블) 선택 후 `schema.name` 등으로 환경 간 비교
- **엑셀 일괄 비교**: 위와 동일 유형으로 목록 일괄 비교 (첫 컬럼 또는 `proc` / `procedure` / `object_id` / `name` 컬럼)
- **공통코드 비교**: `CM_CD_D` 기준으로 기준 환경 대비 갭 비교, 결과 엑셀 다운로드

## CLI 사용법

`dbgit` 패키지가 `src/` 아래에 있으므로, 프로젝트 루트에서 `PYTHONPATH`를 지정합니다.

```
PYTHONPATH=src python -m dbgit schema.proc_name
```

```
PYTHONPATH=src python -m dbgit dbo.vw_Sample --kind view --baseline PRD --envs PRD,STG
```

```
PYTHONPATH=src python -m dbgit dbo.MyTable --kind table --baseline PRD --envs PRD,STG,DEV,QA
```

```
PYTHONPATH=src python -m dbgit 123456 --baseline PRD --envs PRD,STG,DEV,QA
```

## 엑셀 일괄 비교

- 엑셀 첫 번째 컬럼 또는 `proc` / `procedure` / `object_id` / `name` 컬럼을 사용합니다.
- 업로드 후 “일괄 비교 실행”을 누르면 결과 테이블이 표시됩니다.

## 공통코드(CM_CD_D) 비교

- 기준 환경 대비 다른 환경의 갭 차이를 비교합니다.
- 상태(SAME/DIFF/MISSING_IN_ENV/MISSING_IN_BASE)와 차이나는 컬럼을 제공합니다.
- 결과는 화면과 엑셀(`cm_cd_d_diff.xlsx`)로 다운로드할 수 있습니다.
- `TSK_SE_CD` 컬럼은 `CM_CD_M`과 조인해서 표시합니다.

## 출력 예시

```
기준 환경: PRD (dbo.usp_Sample)

환경별 결과:
- PRD: SAME (object_id=123)
- STG: DIFF (object_id=123)
- DEV: SAME (object_id=123)
- QA: DIFF (object_id=123)

차이나는 환경:
STG, QA
```

## 주의

- 실제 비밀번호는 `.env`에만 저장하세요.
- 프로시저가 없으면 에러가 발생합니다.
