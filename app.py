"""
Streamlit 진입 스크립트.

실행: 프로젝트 루트에서 `streamlit run app.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

# 패키지 위치: ./src/dbgit
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from dbgit.st_app import run

run()
