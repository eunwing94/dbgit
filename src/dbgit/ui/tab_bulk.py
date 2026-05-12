"""엑셀 일괄 비교 탭."""

from __future__ import annotations

import streamlit as st

from ..excel_io import extract_proc_ids_from_excel
from ..services.bulk_compare import run_bulk_compare
from ..services.env import load_env_configs
from .diff_view import render_proc_comparison


def render_bulk_compare_tab(envs: list[str], baseline: str) -> None:
    st.caption("엑셀 첫 번째 컬럼 또는 proc/procedure/object_id/name 컬럼을 사용합니다.")
    uploaded = st.file_uploader("엑셀 파일 업로드", type=["xlsx", "xls"])
    if st.button("일괄 비교 실행"):
        if baseline not in envs:
            st.error("기준 환경은 비교 환경 목록에 포함되어야 합니다.")
            return
        if uploaded is None:
            st.error("엑셀 파일을 업로드하세요.")
            return
        try:
            identifiers = extract_proc_ids_from_excel(uploaded)
        except Exception as exc:
            st.error(f"엑셀 읽기 실패: {exc}")
            return
        if not identifiers:
            st.error("엑셀에서 비교할 항목을 찾지 못했습니다.")
            return

        with st.spinner("일괄 비교 중입니다..."):
            try:
                configs = load_env_configs(envs)
            except Exception as exc:
                st.error(f"오류: {exc}")
                return

            outcome = run_bulk_compare(configs, identifiers, baseline, envs)
            st.session_state["bulk_results"] = outcome.results
            st.session_state["bulk_definitions"] = outcome.definitions_map
            st.session_state["bulk_errors"] = outcome.errors

    if st.session_state["bulk_results"]:
        st.subheader("일괄 비교 결과")
        st.dataframe(st.session_state["bulk_results"], use_container_width=True)
        if st.session_state["bulk_errors"]:
            st.warning(
                "오류 항목: " + ", ".join(st.session_state["bulk_errors"].keys())
            )

        options = list(st.session_state["bulk_definitions"].keys())
        if options:
            selected = st.selectbox("상세 비교 대상 선택", options)
            if selected:
                render_proc_comparison(
                    baseline,
                    st.session_state["bulk_definitions"][selected],
                )
