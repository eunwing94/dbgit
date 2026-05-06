"""앱 전역 상수 (CLI·Streamlit 공통)."""

from __future__ import annotations

DEFAULT_ENVS: list[str] = ["PRD", "STG", "DEV", "QA"]

# Streamlit session_state keys
SS_BULK_RESULTS = "bulk_results"
SS_BULK_DEFINITIONS = "bulk_definitions"
SS_BULK_ERRORS = "bulk_errors"
SS_CC_DETAIL_RAW = "cc_detail_raw"
