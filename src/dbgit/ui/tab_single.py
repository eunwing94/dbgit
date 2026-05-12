"""단일 프로시저 비교 탭."""

from __future__ import annotations

import streamlit as st

from ..compare import compare_across_envs
from ..services.env import load_env_configs
from .diff_view import render_proc_comparison


def render_single_compare_tab(envs: list[str], baseline: str) -> None:
    proc_identifier = st.text_input("프로시저/함수 ID 또는 이름", value="")
    if st.button("비교 실행", type="primary"):
        if not proc_identifier.strip():
            st.error("프로시저/함수 ID 또는 이름을 입력하세요.")
            return
        if baseline not in envs:
            st.error("기준 환경은 비교 환경 목록에 포함되어야 합니다.")
            return

        with st.spinner("비교 중입니다..."):
            try:
                configs = load_env_configs(envs)
                definitions = compare_across_envs(configs, proc_identifier.strip())
            except Exception as exc:
                st.error(f"오류: {exc}")
                return

        render_proc_comparison(baseline, definitions)
