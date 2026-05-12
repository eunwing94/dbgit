"""공통코드 CM_CD_D 비교 탭."""

from __future__ import annotations

import streamlit as st

from ..common_code import compare_cm_cd_d
from ..excel_io import build_cm_cd_d_excel_bytes
from ..services.env import load_env_configs


def render_common_code_tab(envs: list[str], baseline: str) -> None:
    st.caption("CM_CD_D 테이블 기준으로 환경별 공통코드 차이를 비교합니다.")
    if st.button("공통코드 비교 실행"):
        if baseline not in envs:
            st.error("기준 환경은 비교 환경 목록에 포함되어야 합니다.")
            return

        with st.spinner("공통코드 비교 중입니다..."):
            try:
                configs = load_env_configs(envs)
                result = compare_cm_cd_d(configs, baseline)
            except Exception as exc:
                st.error(f"오류: {exc}")
                return

        if result.rows.empty:
            st.success("공통코드 조회 결과가 없습니다.")
            return

        st.subheader("공통코드 갭 차이")
        display_rows = result.rows.copy()
        sort_cols = [col for col in display_rows.columns if "SORT_NO" in col]
        for col in sort_cols:
            display_rows[col] = display_rows[col].fillna("").astype(str)
        st.dataframe(display_rows, use_container_width=True)
        excel_bytes = build_cm_cd_d_excel_bytes(display_rows)
        st.download_button(
            "엑셀 다운로드",
            data=excel_bytes,
            file_name="cm_cd_d_diff.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
