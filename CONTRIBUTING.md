# 기여 안내

## 개발 환경

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## 테스트

```bash
pytest
```

`pytest.ini`에서 `pythonpath = src` 로 패키지를 찾습니다.

## 코드 스타일

- DB 접속·비교 로직은 `src/dbgit/` 패키지에 두고, Streamlit 전용 화면은 `streamlit_pages.py`, 진입은 `st_app.py`를 유지합니다.
- 사용자에게 노출되는 문자열은 가능하면 한국어로 통일합니다.

## 커밋 전 체크리스트

1. `pytest` 통과  
2. `.env`·비밀번호가 커밋에 포함되지 않았는지 확인  
