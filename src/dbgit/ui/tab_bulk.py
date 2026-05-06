"""엑셀 일괄 비교 탭."""

from __future__ import annotations

import json

import streamlit as st

from ..bulk_proc import bulk_compare_procedures, extract_proc_ids_from_excel
from ..config import load_env_configs
from ..constants import SS_BULK_DEFINITIONS, SS_BULK_ERRORS, SS_BULK_RESULTS
from .helpers import DATAFRAME_WIDTH_KW, validate_baseline
from .proc_comparison_view import render_proc_comparison


def init_bulk_session_state() -> None:
    st.session_state.setdefault(SS_BULK_RESULTS, [])
    st.session_state.setdefault(SS_BULK_DEFINITIONS, {})
    st.session_state.setdefault(SS_BULK_ERRORS, {})


def tab_bulk(envs: list[str], baseline: str) -> None:
    st.caption("엑셀 첫 번째 컬럼 또는 proc/procedure/object_id/name 컬럼을 사용합니다.")
    uploaded = st.file_uploader("엑셀 파일 업로드", type=["xlsx", "xls"])

    if st.button("일괄 비교 실행"):
        if not validate_baseline(baseline, envs):
            pass
        elif uploaded is None:
            st.error("엑셀 파일을 업로드하세요.")
        else:
            try:
                identifiers = extract_proc_ids_from_excel(uploaded)
            except Exception as exc:
                st.error(f"엑셀 읽기 실패: {exc}")
            else:
                if not identifiers:
                    st.error("엑셀에서 비교할 항목을 찾지 못했습니다.")
                else:
                    with st.spinner("일괄 비교 중입니다..."):
                        try:
                            configs = load_env_configs(envs)
                        except Exception as exc:
                            st.error(f"오류: {exc}")
                        else:
                            results, definitions_map, errors = bulk_compare_procedures(
                                identifiers, configs, baseline, envs
                            )
                            st.session_state[SS_BULK_RESULTS] = results
                            st.session_state[SS_BULK_DEFINITIONS] = definitions_map
                            st.session_state[SS_BULK_ERRORS] = errors

    if not st.session_state.get(SS_BULK_RESULTS):
        return

    st.subheader("일괄 비교 결과")
    st.dataframe(st.session_state[SS_BULK_RESULTS], **DATAFRAME_WIDTH_KW)
    errs = st.session_state.get(SS_BULK_ERRORS) or {}
    if errs:
        st.warning("오류 항목: " + ", ".join(errs.keys()))

    bulk_json = json.dumps(
        {
            "baseline": baseline,
            "summary": st.session_state[SS_BULK_RESULTS],
            "errors": errs,
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )
    with st.expander("일괄 결과 JSON"):
        st.code(bulk_json, language="json")
        st.download_button(
            "일괄 결과 JSON 다운로드",
            data=bulk_json.encode("utf-8"),
            file_name="bulk_proc_comparison.json",
            mime="application/json",
            key="bulk_summary_json_dl",
        )

    definitions_map = st.session_state[SS_BULK_DEFINITIONS]
    options = list(definitions_map.keys())
    if not options:
        return
    selected = st.selectbox("상세 비교 대상 선택", options)
    if selected:
        render_proc_comparison(
            baseline,
            definitions_map[selected],
            widget_suffix=f"bulk_{selected}",
        )
