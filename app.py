from __future__ import annotations

import os
import sys
import re
import difflib
from pathlib import Path
from io import BytesIO
from typing import Dict, List

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dbgit.compare import compare_across_envs
from dbgit.common_code import compare_cm_cd_d
from dbgit.config import EnvConfig, load_env_config
from dbgit.pdf_unlock import PdfPasswordError, strip_pdf_encryption


DEFAULT_ENVS = ["PRD", "STG", "DEV", "QA"]


def _load_configs(envs: List[str]) -> List[EnvConfig]:
    configs: List[EnvConfig] = []
    for env_name in envs:
        configs.append(load_env_config(env_name))
    return configs


def _render_results(baseline: str, definitions: Dict[str, object]) -> None:
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

    diff_envs = [
        env_name
        for env_name, proc_def in definitions.items()
        if proc_def.digest != base_def.digest
    ]
    if diff_envs:
        with st.expander("차이 상세 (공백/빈줄 무시)"):
            base_lines = _build_comparable_lines(base_def.definition)
            for env_name in diff_envs:
                proc_def = definitions[env_name]
                env_lines = _build_comparable_lines(proc_def.definition)
                base_text, env_text = _build_diff_text(
                    base_lines,
                    env_lines,
                )
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


def _build_comparable_lines(definition: str) -> List[tuple[int, str, str]]:
    lines = []
    for idx, line in enumerate(definition.splitlines(), start=1):
        normalized = re.sub(r"\s+", "", line)
        if not normalized:
            continue
        lines.append((idx, line, normalized))
    return lines


def _format_line_range(lines: List[tuple[int, str, str]]) -> str:
    if not lines:
        return "-"
    start = lines[0][0]
    end = lines[-1][0]
    if start == end:
        return f"L{start}"
    return f"L{start}-L{end}"


def _format_chunk(header: str, lines: List[tuple[int, str, str]]) -> List[str]:
    output = [header]
    if not lines:
        output.append("(없음)")
        return output
    for line_no, text, _ in lines:
        output.append(f"L{line_no}: {text}")
    return output


def _build_diff_text(
    base_lines: List[tuple[int, str, str]],
    env_lines: List[tuple[int, str, str]],
) -> tuple[str, str]:
    base_norm = [item[2] for item in base_lines]
    env_norm = [item[2] for item in env_lines]
    matcher = difflib.SequenceMatcher(a=base_norm, b=env_norm, autojunk=False)

    base_out: List[str] = []
    env_out: List[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        base_chunk = base_lines[i1:i2]
        env_chunk = env_lines[j1:j2]
        header = f"[{tag}] base {_format_line_range(base_chunk)} | env {_format_line_range(env_chunk)}"
        base_out.extend(_format_chunk(header, base_chunk))
        env_out.extend(_format_chunk(header, env_chunk))
        base_out.append("")
        env_out.append("")

    return "\n".join(base_out).strip(), "\n".join(env_out).strip()


def _extract_proc_ids(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> List[str]:
    df = pd.read_excel(uploaded_file)
    if df.empty:
        return []
    for candidate in ("proc", "procedure", "object_id", "name"):
        if candidate in df.columns:
            series = df[candidate]
            break
    else:
        series = df.iloc[:, 0]
    values = []
    for item in series.tolist():
        if item is None or (isinstance(item, float) and pd.isna(item)):
            continue
        text = str(item).strip()
        if text:
            values.append(text)
    return values


def _init_state() -> None:
    st.session_state.setdefault("bulk_results", [])
    st.session_state.setdefault("bulk_definitions", {})
    st.session_state.setdefault("bulk_errors", {})


def _safe_pdf_base_name(name: str | None) -> str:
    if not name or not str(name).strip():
        return "document"
    base = Path(str(name)).name
    if base.lower().endswith(".pdf"):
        base = base[:-4]
    return base or "document"


def _build_excel_bytes(result_df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False, sheet_name="CM_CD_D_DIFF")
    buffer.seek(0)
    return buffer.read()


def main() -> None:
    st.set_page_config(page_title="DB 프로시저 비교", layout="wide")
    st.title("DB 프로시저 형상 비교")

    _init_state()
    st.info("프로시저/함수 object_id 또는 schema.name을 입력하세요.")

    dotenv_path = st.text_input("dotenv 경로", value=".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path, override=True)
    else:
        st.warning("dotenv 파일을 찾지 못했습니다. 환경변수가 직접 설정되어 있어야 합니다.")

    envs = st.multiselect("비교할 환경", DEFAULT_ENVS, default=DEFAULT_ENVS)
    baseline = st.selectbox("기준 환경", envs or DEFAULT_ENVS, index=0)

    tabs = st.tabs(
        ["단일 비교", "엑셀 일괄 비교", "공통코드 비교", "PDF 암호 제거"]
    )

    with tabs[0]:
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
                    configs = _load_configs(envs)
                    definitions = compare_across_envs(configs, proc_identifier.strip())
                except Exception as exc:
                    st.error(f"오류: {exc}")
                    return

            _render_results(baseline, definitions)

    with tabs[1]:
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
                identifiers = _extract_proc_ids(uploaded)
            except Exception as exc:
                st.error(f"엑셀 읽기 실패: {exc}")
                return
            if not identifiers:
                st.error("엑셀에서 비교할 항목을 찾지 못했습니다.")
                return

            with st.spinner("일괄 비교 중입니다..."):
                try:
                    configs = _load_configs(envs)
                except Exception as exc:
                    st.error(f"오류: {exc}")
                    return

                results = []
                definitions_map: Dict[str, Dict[str, object]] = {}
                errors: Dict[str, str] = {}
                for identifier in identifiers:
                    try:
                        definitions = compare_across_envs(configs, identifier)
                        definitions_map[identifier] = definitions
                        base_def = definitions[baseline]
                        row = {"대상": identifier}
                        any_diff = False
                        for env_name, proc_def in definitions.items():
                            status = "SAME" if proc_def.digest == base_def.digest else "DIFF"
                            row[env_name] = status
                            if status == "DIFF":
                                any_diff = True
                        row["상태"] = "DIFF" if any_diff else "SAME"
                        results.append(row)
                    except Exception as exc:
                        errors[identifier] = str(exc)
                        row = {"대상": identifier, "상태": "ERROR"}
                        for env_name in envs:
                            row[env_name] = "ERROR"
                        results.append(row)

                st.session_state["bulk_results"] = results
                st.session_state["bulk_definitions"] = definitions_map
                st.session_state["bulk_errors"] = errors

        if st.session_state["bulk_results"]:
            st.subheader("일괄 비교 결과")
            st.dataframe(st.session_state["bulk_results"], use_container_width=True)
            if st.session_state["bulk_errors"]:
                st.warning(
                    "오류 항목: "
                    + ", ".join(st.session_state["bulk_errors"].keys())
                )

            options = list(st.session_state["bulk_definitions"].keys())
            if options:
                selected = st.selectbox("상세 비교 대상 선택", options)
                if selected:
                    _render_results(
                        baseline,
                        st.session_state["bulk_definitions"][selected],
                    )

    with tabs[2]:
        st.caption("CM_CD_D 테이블 기준으로 환경별 공통코드 차이를 비교합니다.")
        if st.button("공통코드 비교 실행"):
            if baseline not in envs:
                st.error("기준 환경은 비교 환경 목록에 포함되어야 합니다.")
                return

            with st.spinner("공통코드 비교 중입니다..."):
                try:
                    configs = _load_configs(envs)
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
            excel_bytes = _build_excel_bytes(display_rows)
            st.download_button(
                "엑셀 다운로드",
                data=excel_bytes,
                file_name="cm_cd_d_diff.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with tabs[3]:
        st.caption(
            "열람 권한이 있는 PDF만 다루세요. 알고 있는 암호로 연 뒤, 암호 없는 PDF로 다시 저장합니다."
        )
        pdf_up = st.file_uploader("암호가 걸린 PDF", type=["pdf"], key="pdf_unlock_upload")
        pdf_password = st.text_input("PDF 열람 암호", type="password", key="pdf_unlock_password")

        if pdf_up is None:
            st.session_state.pop("pdf_unlock_bytes", None)
            st.session_state.pop("pdf_unlock_download_name", None)

        if st.button("암호 제거 PDF 만들기", type="secondary", key="pdf_unlock_run"):
            if pdf_up is None:
                st.error("PDF 파일을 업로드하세요.")
            else:
                try:
                    out = strip_pdf_encryption(pdf_up.getvalue(), pdf_password)
                except PdfPasswordError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"PDF 처리 실패: {exc}")
                else:
                    st.session_state["pdf_unlock_bytes"] = out
                    st.session_state["pdf_unlock_download_name"] = (
                        f"{_safe_pdf_base_name(pdf_up.name)}_unlocked.pdf"
                    )
                    st.success("암호가 제거된 PDF를 준비했습니다. 아래에서 다운로드하세요.")

        unlock_bytes = st.session_state.get("pdf_unlock_bytes")
        unlock_name = st.session_state.get("pdf_unlock_download_name")
        if unlock_bytes and unlock_name:
            st.download_button(
                label="암호 제거 PDF 다운로드",
                data=unlock_bytes,
                file_name=unlock_name,
                mime="application/pdf",
                key="pdf_unlock_download",
            )


if __name__ == "__main__":
    main()
