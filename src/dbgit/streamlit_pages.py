"""Streamlit 위젯·탭 화면 (비즈니스 로직은 compare/common_code/output_format 등에서 import)."""

from __future__ import annotations

import json
import os
from typing import Dict, List

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from .bulk_proc import bulk_compare_procedures, extract_proc_ids_from_excel
from .common_code import compare_cm_cd_d
from .common_code_filters import build_common_code_summary, filter_common_code_df
from .compare import ProcDefinition, compare_across_envs
from .config import EnvConfig, load_env_config
from .diff_text import build_comparable_lines, build_diff_text
from .excel_export import common_code_two_sheet_bytes, stringify_sort_no_columns
from .output_format import format_proc_comparison_json, proc_comparison_payload

DEFAULT_ENVS = ["PRD", "STG", "DEV", "QA"]
_DATAFRAME_WIDTH_KW = {"width": "stretch"}


def _load_configs(envs: List[str]) -> List[EnvConfig]:
    return [load_env_config(name) for name in envs]


def _validate_baseline(baseline: str, envs: List[str]) -> bool:
    if baseline not in envs:
        st.error("기준 환경은 비교 환경 목록에 포함되어야 합니다.")
        return False
    return True


def _init_bulk_session_state() -> None:
    st.session_state.setdefault("bulk_results", [])
    st.session_state.setdefault("bulk_definitions", {})
    st.session_state.setdefault("bulk_errors", {})


def _render_proc_comparison(
    baseline: str,
    definitions: Dict[str, ProcDefinition],
    *,
    widget_suffix: str = "proc",
) -> None:
    base_def = definitions[baseline]
    st.subheader("비교 결과")
    st.caption(f"기준 환경: {baseline} ({base_def.full_name})")

    rows = [
        {
            "환경": env_name,
            "상태": "SAME" if proc_def.digest == base_def.digest else "DIFF",
            "object_id": proc_def.object_id,
        }
        for env_name, proc_def in definitions.items()
    ]
    st.dataframe(rows, **_DATAFRAME_WIDTH_KW)

    diff_envs = [
        env_name
        for env_name, proc_def in definitions.items()
        if proc_def.digest != base_def.digest
    ]
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


def _tab_single(envs: List[str], baseline: str) -> None:
    proc_identifier = st.text_input("프로시저/함수 ID 또는 이름", value="")
    if not st.button("비교 실행", type="primary"):
        return
    if not proc_identifier.strip():
        st.error("프로시저/함수 ID 또는 이름을 입력하세요.")
        return
    if not _validate_baseline(baseline, envs):
        return

    with st.spinner("비교 중입니다..."):
        try:
            configs = _load_configs(envs)
            definitions = compare_across_envs(configs, proc_identifier.strip())
        except Exception as exc:
            st.error(f"오류: {exc}")
            return

    _render_proc_comparison(baseline, definitions, widget_suffix="single")


def _tab_bulk(envs: List[str], baseline: str) -> None:
    st.caption("엑셀 첫 번째 컬럼 또는 proc/procedure/object_id/name 컬럼을 사용합니다.")
    uploaded = st.file_uploader("엑셀 파일 업로드", type=["xlsx", "xls"])

    if st.button("일괄 비교 실행"):
        if not _validate_baseline(baseline, envs):
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
                            configs = _load_configs(envs)
                        except Exception as exc:
                            st.error(f"오류: {exc}")
                        else:
                            results, definitions_map, errors = bulk_compare_procedures(
                                identifiers, configs, baseline, envs
                            )
                            st.session_state["bulk_results"] = results
                            st.session_state["bulk_definitions"] = definitions_map
                            st.session_state["bulk_errors"] = errors

    if not st.session_state.get("bulk_results"):
        return

    st.subheader("일괄 비교 결과")
    st.dataframe(st.session_state["bulk_results"], **_DATAFRAME_WIDTH_KW)
    if st.session_state.get("bulk_errors"):
        st.warning("오류 항목: " + ", ".join(st.session_state["bulk_errors"].keys()))

    bulk_json = json.dumps(
        {
            "baseline": baseline,
            "summary": st.session_state["bulk_results"],
            "errors": st.session_state.get("bulk_errors", {}),
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

    options = list(st.session_state["bulk_definitions"].keys())
    if not options:
        return
    selected = st.selectbox("상세 비교 대상 선택", options)
    if selected:
        _render_proc_comparison(
            baseline,
            st.session_state["bulk_definitions"][selected],
            widget_suffix=f"bulk_{selected}",
        )


def _tab_common_code(envs: List[str], baseline: str) -> None:
    st.caption("CM_CD_D 테이블 기준으로 환경별 공통코드 차이를 비교합니다.")
    if st.button("공통코드 비교 실행"):
        if not _validate_baseline(baseline, envs):
            return

        with st.spinner("공통코드 비교 중입니다..."):
            try:
                configs = _load_configs(envs)
                result = compare_cm_cd_d(configs, baseline)
            except Exception as exc:
                st.error(f"오류: {exc}")
                return

        st.session_state["cc_detail_raw"] = result.rows.copy()

    raw = st.session_state.get("cc_detail_raw")
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
    st.dataframe(display_rows, **_DATAFRAME_WIDTH_KW)

    summary_df = build_common_code_summary(filtered)
    excel_bytes = common_code_two_sheet_bytes(summary_df, display_rows)
    st.download_button(
        "엑셀 다운로드 (요약·상세 시트)",
        data=excel_bytes,
        file_name="cm_cd_d_diff.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def run_main() -> None:
    st.set_page_config(page_title="DB 프로시저 비교", layout="wide")
    st.title("DB 프로시저 형상 비교")
    st.info("프로시저/함수 object_id 또는 schema.name을 입력하세요.")

    _init_bulk_session_state()

    dotenv_path = st.text_input("dotenv 경로", value=".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path, override=True)
    else:
        st.warning("dotenv 파일을 찾지 못했습니다. 환경변수가 직접 설정되어 있어야 합니다.")

    envs = st.multiselect("비교할 환경", DEFAULT_ENVS, default=DEFAULT_ENVS)
    baseline = st.selectbox("기준 환경", envs or DEFAULT_ENVS, index=0)

    tabs = st.tabs(["단일 비교", "엑셀 일괄 비교", "공통코드 비교"])
    with tabs[0]:
        _tab_single(envs, baseline)
    with tabs[1]:
        _tab_bulk(envs, baseline)
    with tabs[2]:
        _tab_common_code(envs, baseline)
