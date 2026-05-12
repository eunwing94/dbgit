"""Streamlit 진입 스크립트. 로직은 `dbgit.ui` 패키지에 둡니다."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dbgit.ui import run_streamlit_app


def main() -> None:
    run_streamlit_app()


if __name__ == "__main__":
    main()
