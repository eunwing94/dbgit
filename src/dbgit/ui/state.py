"""Streamlit session_state 초기화."""

from __future__ import annotations

import streamlit as st


def init_session_state() -> None:
    """일괄 비교·PDF 탭에서 쓰는 session_state 기본값."""
    st.session_state.setdefault("bulk_results", [])
    st.session_state.setdefault("bulk_definitions", {})
    st.session_state.setdefault("bulk_errors", {})
