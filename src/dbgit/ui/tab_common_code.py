"""CM_CD_D 공통코드 비교 탭."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..common_code import compare_cm_cd_d
from ..common_code_filters import build_common_code_summary, filter_common_code_df
from ..config import load_env_configs
from ..constants import SS_CC_DETAIL_RAW
from ..excel_export import common_code_two_sheet_bytes, stringify_sort_no_columns
from .helpers import DATAFRAME_WIDTH_KW, validate_baseline


def tab_common_code(envs: list[str], baseline: str) -> None:
    st.caption("CM_CD_D 테이블 기준으로 환경별 공통코드 차이를 비교합니다.")
    if st.button("공통코드 비교 실행"):
        if not validate_baseline(baseline, envs):
            return

        with st.spinner("공통코드 비교 중입니다..."):
            try:
                configs = load_env_configs(envs)
                result = compare_cm_cd_d(configs, baseline)
            except Exception as exc:
                st.error(f"오류: {exc}")
                return

        st.session_state[SS_CC_DETAIL_RAW] = result.rows.copy()

    raw = st.session_state.get(SS_CC_DETAIL_RAW)
    if raw is None or (isinstance(raw, pd.DataFrame) and raw.empty):
        if raw is not None and isinstance(raw, pd.DataFrame) and raw.empty:
            st.success("공통코드 조회 결과가 없습니다.")
        return

    st.subheader("공통코드 갭 차이")

    hide_same = st.checkbox("SAME 행 숨기기", value=False, key="cc_hide_same")
    comp_pf = st.text_input("COMP_CD 접두어 필터 (선택)", value="", key="cc_comp_pf")
    cm_pf = st.text_input("CM_CD 접두어 필터 (선택)", value="", key="cc_cm_pf")

    filtered = filter_common_code_df(
        raw,
        hide_same=hide_same,
        comp_cd_prefix=comp_pf,
        cm_cd_prefix=cm_pf,
    )
    display_rows = stringify_sort_no_columns(filtered)
    st.dataframe(display_rows, **DATAFRAME_WIDTH_KW)

    summary_df = build_common_code_summary(filtered)
    excel_bytes = common_code_two_sheet_bytes(summary_df, display_rows)
    st.download_button(
        "엑셀 다운로드 (요약·상세 시트)",
        data=excel_bytes,
        file_name="cm_cd_d_diff.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
