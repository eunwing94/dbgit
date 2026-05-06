"""단일·일괄 비교 결과 패널."""

from __future__ import annotations

from typing import Dict

import streamlit as st

from ..compare import ProcDefinition
from ..diff_text import build_comparable_lines, build_diff_text
from ..output_format import (
    diff_environment_names,
    format_proc_comparison_json,
    proc_comparison_payload,
    proc_comparison_summary_rows,
)
from .helpers import DATAFRAME_WIDTH_KW


def render_proc_comparison(
    baseline: str,
    definitions: Dict[str, ProcDefinition],
    *,
    widget_suffix: str = "proc",
) -> None:
    base_def = definitions[baseline]
    st.subheader("비교 결과")
    st.caption(f"기준 환경: {baseline} ({base_def.full_name})")

    rows = proc_comparison_summary_rows(baseline, definitions)
    st.dataframe(rows, **DATAFRAME_WIDTH_KW)

    diff_envs = diff_environment_names(baseline, definitions)
    if diff_envs:
        st.warning(f"차이나는 환경: {', '.join(diff_envs)}")
    else:
        st.success("모든 환경이 동일합니다.")

    json_text = format_proc_comparison_json(baseline, definitions)
    with st.expander("결과 JSON (복사·다운로드)", expanded=False):
        st.code(json_text, language="json")
        st.download_button(
            "JSON 파일 다운로드",
            data=json_text.encode("utf-8"),
            file_name="proc_comparison.json",
            mime="application/json",
            key=f"dl_proc_json_{widget_suffix}",
        )
        st.json(proc_comparison_payload(baseline, definitions))

    with st.expander("환경별 프로시저 정의 보기"):
        for env_name, proc_def in definitions.items():
            st.markdown(f"**{env_name}** ({proc_def.full_name})")
            st.text_area(
                label=f"{env_name} definition",
                value=proc_def.definition or "",
                height=200,
                key=f"def_{env_name}",
            )

    if not diff_envs:
        return

    with st.expander("차이 상세 (공백/빈줄 무시)"):
        base_lines = build_comparable_lines(base_def.definition)
        for env_name in diff_envs:
            proc_def = definitions[env_name]
            env_lines = build_comparable_lines(proc_def.definition)
            base_text, env_text = build_diff_text(base_lines, env_lines)
            st.markdown(f"**{env_name}**")
            cols = st.columns(2)
            cols[0].text_area(
                label=f"기준({baseline})",
                value=base_text,
                height=220,
                key=f"diff_base_{env_name}",
            )
            cols[1].text_area(
                label=f"{env_name}",
                value=env_text,
                height=220,
                key=f"diff_env_{env_name}",
            )
