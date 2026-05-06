"""Streamlit 앱 진입: 로깅 초기화 후 화면 모듈로 위임."""

from __future__ import annotations

from .logging_setup import configure_logging
from .ui import run_main


def run() -> None:
    configure_logging()
    run_main()
