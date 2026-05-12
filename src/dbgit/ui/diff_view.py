"""Streamlit: 프로시저 환경 간 비교 결과 표시."""

from __future__ import annotations

from typing import Dict

import streamlit as st

from ..compare import ProcDefinition
from ..text_diff import build_comparable_lines, build_diff_text


def render_proc_comparison(baseline: str, definitions: Dict[str, ProcDefinition]) -> None:
    """동일 식별자에 대한 환경별 정의·요약·텍스트 diff를 렌더링합니다."""
    base_def = definitions[baseline]
    st.subheader("비교 결과")
    st.caption(f"기준 환경: {baseline} ({base_def.full_name})")

    rows = []
    for env_name, proc_def in definitions.items():
        rows.append(
            {
                "환경": env_name,
                "상태": "SAME" if proc_def.digest == base_def.digest else "DIFF",
                "object_id": proc_def.object_id,
            }
        )
    st.dataframe(rows, use_container_width=True)

    diff_envs = [
        env_name
        for env_name, proc_def in definitions.items()
        if proc_def.digest != base_def.digest
    ]
    if diff_envs:
        st.warning(f"차이나는 환경: {', '.join(diff_envs)}")
    else:
        st.success("모든 환경이 동일합니다.")

    with st.expander("환경별 프로시저 정의 보기"):
        for env_name, proc_def in definitions.items():
            st.markdown(f"**{env_name}** ({proc_def.full_name})")
            st.text_area(
                label=f"{env_name} definition",
                value=proc_def.definition or "",
                height=200,
                key=f"def_{env_name}",
            )

    if diff_envs:
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
