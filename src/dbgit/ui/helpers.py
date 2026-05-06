"""Streamlit 전용 소형 헬퍼."""

from __future__ import annotations

import streamlit as st

DATAFRAME_WIDTH_KW = {"width": "stretch"}


def validate_baseline(baseline: str, envs: list[str]) -> bool:
    if baseline not in envs:
        st.error("기준 환경은 비교 환경 목록에 포함되어야 합니다.")
        return False
    return True
