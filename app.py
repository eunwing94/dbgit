from __future__ import annotations

import sys
import re
import difflib
from pathlib import Path
from io import BytesIO
from typing import Dict, List, cast

import pandas as pd
import pyodbc
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dbgit.compare import (
    ObjectKind,
    compare_across_envs,
    compare_many_across_envs_by_object_id,
    compare_many_across_envs_by_qualified_module_name,
    compare_many_across_envs_by_qualified_table_name,
)
from dbgit.common_code import compare_cm_cd_d
from dbgit.config import EnvConfig, load_env_config
from dbgit.db import open_connection
from dbgit.object_search import search_objects


DEFAULT_ENVS = ["PRD", "STG", "DEV", "QA"]


def _resolve_dotenv_path(user_path: str) -> Path:
    """Streamlit 실행 cwd와 무관하게 프로젝트 루트 기준으로 .env 경로를 잡습니다."""
    p = Path(user_path.strip() or ".env")
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return p


def _load_configs(envs: List[str]) -> List[EnvConfig]:
    configs: List[EnvConfig] = []
    for env_name in envs:
        configs.append(load_env_config(env_name))
    return configs


def _render_results(
    baseline: str,
    definitions: Dict[str, object],
    object_kind: str = "routine",
    *,
    widget_scope: str = "default",
) -> None:
    base_def = definitions[baseline]
    st.subheader("비교 결과")
    st.caption(f"기준 환경: {baseline} ({base_def.full_name})")

    labels = {
        "routine": ("환경별 프로시저·함수 정의", "차이 상세 (공백/빈줄 무시)"),
        "view": ("환경별 뷰 정의", "차이 상세 (공백/빈줄 무시)"),
        "table": (
            "환경별 테이블 컬럼 스키마 (컬럼별 파이프 구분)",
            "차이 상세 (컬럼 줄 단위, 공백 무시)",
        ),
    }
    exp_def_title, exp_diff_title = labels.get(object_kind, labels["routine"])
    sk = f"{widget_scope}_"

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

    with st.expander(exp_def_title):
        for env_name, proc_def in definitions.items():
            st.markdown(f"**{env_name}** ({proc_def.full_name})")
            st.text_area(
                label=f"{env_name} definition",
                value=proc_def.definition or "",
                height=200,
                key=f"{sk}def_{env_name}_{object_kind}",
            )

    diff_envs = [
        env_name
        for env_name, proc_def in definitions.items()
        if proc_def.digest != base_def.digest
    ]
    if diff_envs:
        with st.expander(exp_diff_title):
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
                    key=f"{sk}diff_base_{env_name}_{object_kind}",
                )
                cols[1].text_area(
                    label=f"{env_name}",
                    value=env_text,
                    height=220,
                    key=f"{sk}diff_env_{env_name}_{object_kind}",
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


def _read_bulk_excel_first_sheet(uploaded: object) -> pd.DataFrame:
    """첫 번째 시트만 읽습니다."""
    return pd.read_excel(BytesIO(uploaded.getvalue()))


def _first_column_identifiers(df: pd.DataFrame) -> List[str]:
    """첫 번째 열의 비어 있지 않은 값을 위에서부터 수집합니다."""
    if df.empty or df.shape[1] < 1:
        return []
    col = df.iloc[:, 0]
    out: List[str] = []
    for v in col.tolist():
        if v is None or (isinstance(v, float) and pd.isna(v)):
            continue
        s = str(v).strip()
        if s:
            out.append(s)
    return out


def _init_state() -> None:
    st.session_state.setdefault("bulk_results", [])
    st.session_state.setdefault("bulk_definitions", {})
    st.session_state.setdefault("bulk_errors", {})
    st.session_state.setdefault("bulk_object_kind", "routine")
    st.session_state.setdefault("single_identifier", "")
    st.session_state.setdefault("obj_search_hits", [])


def _build_excel_bytes(result_df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False, sheet_name="CM_CD_D_DIFF")
    buffer.seek(0)
    return buffer.read()


def _build_object_search_excel_bytes(hits: list) -> bytes:
    """객체 검색 결과 목록을 xlsx로 직렬화합니다. 컬럼 순서: 비교유형, sys_type, object_id, 이름."""
    rows = [
        {
            "비교유형": h.compare_kind,
            "sys_type": h.sql_type,
            "object_id": h.object_id,
            "이름": h.name,
        }
        for h in hits
    ]
    df = pd.DataFrame(rows, columns=["비교유형", "sys_type", "object_id", "이름"])
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="object_search")
    buffer.seek(0)
    return buffer.read()


def main() -> None:
    st.set_page_config(page_title="DB 프로시저 비교", layout="wide")
    st.title("DB 프로시저 형상 비교")

    _init_state()
    st.info(
        "프로시저·함수·뷰는 `sys.sql_modules` 본문을, "
        "사용자 테이블은 컬럼·타입·NULL·IDENTITY·계산열 정의 메타를 환경별로 비교합니다. "
        "식별자는 object_id 또는 schema.name 형식을 권장합니다."
    )

    dotenv_path = st.text_input("dotenv 경로", value=".env", help="프로젝트 루트 기준 상대 경로이거나, 절대 경로를 넣을 수 있습니다.")
    resolved = _resolve_dotenv_path(dotenv_path)
    if resolved.is_file():
        load_dotenv(resolved, override=True)
        st.caption(f"환경 변수 파일 로드: `{resolved}`")
    else:
        example = PROJECT_ROOT / ".env.example"
        lines = [
            f"`{resolved}` 파일이 없습니다.",
            "DB 비교를 하려면 프로젝트 루트에 `.env`를 두고 `PRD_HOST` 등을 채우세요.",
        ]
        if example.is_file():
            lines.append(
                f"샘플: 터미널에서 프로젝트 루트로 이동한 뒤 `cp .env.example .env` 후 `.env`를 편집하세요."
            )
        lines.append(
            "이미 터미널·IDE·OS에 동일 이름의 환경변수를 넣었다면 `.env` 없이도 동작할 수 있습니다."
        )
        st.info(" ".join(lines))

    envs = st.multiselect("비교할 환경", DEFAULT_ENVS, default=DEFAULT_ENVS)
    baseline = st.selectbox("기준 환경", envs or DEFAULT_ENVS, index=0)
    object_kind = st.radio(
        "비교 대상 유형",
        options=["routine", "view", "table"],
        format_func=lambda k: {
            "routine": "프로시저·함수 (P, PC, FN, IF, TF)",
            "view": "뷰 (V)",
            "table": "테이블 (U, 컬럼 스키마)",
        }[k],
        horizontal=True,
        key="object_kind",
    )

    tabs = st.tabs(["객체 검색", "단일 비교", "엑셀 일괄 비교", "공통코드 비교"])

    with tabs[0]:
        st.subheader("객체 검색")
        st.caption(
            f"**{baseline}** DB 기준으로 조회합니다. 이름·본문(정의)에 검색어가 포함된 객체를 찾습니다. "
            "대량 DB에서는 본문 검색이 다소 느릴 수 있습니다."
        )
        q_needle = st.text_input(
            "검색어",
            value="",
            key="obj_search_needle",
            placeholder="예: SA | usp_Order 또는  foo OR bar",
            help="여러 단어는 ` OR ` 또는 `|` 로 나누면 됩니다. (대소문자 무시) 한 토큰이라도 이름·본문에 맞으면 조회됩니다.",
        )
        c1, c2 = st.columns(2)
        with c1:
            inc_name = st.checkbox("이름에 포함", value=True, key="obj_search_name")
        with c2:
            inc_body = st.checkbox("본문·컬럼에 포함", value=True, key="obj_search_body")
        st.markdown("**대상 유형**")
        c3, c4, c5 = st.columns(3)
        with c3:
            sr_routine = st.checkbox("프로시저·함수", value=True, key="obj_search_routine")
        with c4:
            sr_view = st.checkbox("뷰", value=True, key="obj_search_view")
        with c5:
            sr_table = st.checkbox("테이블", value=True, key="obj_search_table")

        if st.button("조회", type="secondary", key="obj_search_run"):
            if not q_needle.strip():
                st.error("검색어를 입력하세요.")
            elif baseline not in envs:
                st.error("기준 환경을 비교 환경 목록에 포함하세요.")
            elif not inc_name and not inc_body:
                st.error("이름 또는 본문·컬럼 검색을 하나 이상 켜 주세요.")
            elif not sr_routine and not sr_view and not sr_table:
                st.error("대상 유형을 하나 이상 선택하세요.")
            else:
                try:
                    base_cfg = load_env_config(baseline)
                    outcome = search_objects(
                        base_cfg,
                        needle=q_needle,
                        include_name=inc_name,
                        include_definition=inc_body,
                        include_routine=sr_routine,
                        include_view=sr_view,
                        include_table=sr_table,
                    )
                except Exception as exc:
                    st.error(f"조회 실패: {exc}")
                else:
                    st.session_state["obj_search_hits"] = outcome.hits
                    st.session_state["obj_search_display_trunc"] = len(outcome.hits) > 500
                    st.session_state["obj_search_sql_cap_hit"] = outcome.reached_sql_fetch_cap
                    st.session_state["obj_search_sql_cap"] = outcome.sql_fetch_cap

        hits = st.session_state.get("obj_search_hits") or []
        if hits:
            display = hits[:500]
            if st.session_state.get("obj_search_display_trunc"):
                st.warning(
                    f"화면과 아래 선택 목록은 500건까지입니다(총 {len(hits):,}건). "
                    "**엑셀·CSV**에는 조회된 전체가 포함됩니다."
                )
            if st.session_state.get("obj_search_sql_cap_hit"):
                cap = int(st.session_state.get("obj_search_sql_cap") or 100_000)
                st.warning(
                    f"한 번의 SQL 조회가 상한({cap:,}행)에 도달했을 수 있습니다. "
                    "더 필요하면 검색어를 좁히거나 환경변수 `DBGIT_OBJECT_SEARCH_SQL_CAP`을 조정하세요."
                )
            df_h = pd.DataFrame(
                [
                    {
                        "유형": h.compare_kind,
                        "schema": h.schema_name,
                        "이름": h.name,
                        "object_id": h.object_id,
                        "전체이름": h.full_name,
                    }
                    for h in display
                ]
            )
            df_export = pd.DataFrame(
                [
                    {
                        "유형": h.compare_kind,
                        "schema": h.schema_name,
                        "이름": h.name,
                        "object_id": h.object_id,
                        "전체이름": h.full_name,
                    }
                    for h in hits
                ]
            )
            safe_base = "".join(ch if str(ch).isalnum() else "_" for ch in str(baseline))[:40] or "env"
            xlsx_bytes = _build_object_search_excel_bytes(hits)
            csv_bytes = df_export.to_csv(index=False).encode("utf-8-sig")

            st.markdown(f"**조회 결과 보내기** (엑셀·CSV: 전체 **{len(hits):,}**건)")
            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button(
                    label="엑셀 (.xlsx) 다운로드",
                    data=xlsx_bytes,
                    file_name=f"object_search_{safe_base}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="obj_search_xlsx",
                    type="primary",
                )
            with dl2:
                st.download_button(
                    label="CSV (.csv) 다운로드",
                    data=csv_bytes,
                    file_name=f"object_search_{safe_base}.csv",
                    mime="text/csv",
                    key="obj_search_csv",
                )

            st.dataframe(df_h, use_container_width=True, height=280)
            pick_label = st.selectbox(
                "단일 비교에 사용할 객체 선택",
                options=[h.full_name for h in display],
                key="obj_search_pick",
            )
            picked = next(h for h in display if h.full_name == pick_label)
            if st.button("선택 객체를 단일 비교에 반영", key="obj_search_apply"):
                st.session_state["single_identifier"] = picked.full_name
                st.session_state["object_kind"] = picked.compare_kind
                st.session_state["apply_from_search_msg"] = (
                    f"'단일 비교' 탭으로 이동한 뒤 **비교 실행**을 누르세요. "
                    f"(`{picked.full_name}`, 유형 `{picked.compare_kind}`)"
                )
                st.rerun()

    with tabs[1]:
        st.subheader("단일 비교")
        flash = st.session_state.pop("apply_from_search_msg", None)
        if flash:
            st.success(flash)
        proc_identifier = st.text_input(
            "객체 ID 또는 이름 (schema.name 권장)",
            key="single_identifier",
        )
        if st.button("비교 실행", type="primary", key="single_compare_run"):
            st.session_state.pop("single_compare_result", None)
            if not proc_identifier.strip():
                st.error("객체 ID 또는 이름을 입력하세요.")
            elif baseline not in envs:
                st.error("기준 환경은 비교 환경 목록에 포함되어야 합니다.")
            else:
                with st.spinner("비교 중입니다..."):
                    try:
                        configs = _load_configs(envs)
                        definitions = compare_across_envs(
                            configs,
                            proc_identifier.strip(),
                            object_kind=object_kind,
                        )
                    except Exception as exc:
                        st.error(f"오류: {exc}")
                    else:
                        st.session_state["single_compare_result"] = (
                            baseline,
                            definitions,
                            object_kind,
                        )

        res = st.session_state.get("single_compare_result")
        if res:
            b, defs, okind = res
            _render_results(b, defs, okind, widget_scope="single_compare")

    with tabs[2]:
        st.subheader("엑셀 일괄 비교")
        bulk_help = {
            "routine": (
                "첫 번째 열에 **프로시저·함수 이름**을 한 줄에 하나씩 넣습니다. "
                "각 환경에서 `sys.sql_modules` 본문이 기준 환경과 같은지 비교합니다. "
                "`schema.이름` 또는 `object_id`(숫자)를 권장합니다. 짧은 이름만 넣으면 동일 이름이 여러 스키마에 있을 때 임의로 하나가 선택될 수 있습니다."
            ),
            "view": (
                "첫 번째 열에 **뷰 이름**을 한 줄에 하나씩 넣습니다. "
                "각 환경에서 뷰 정의(`sys.sql_modules`)가 기준 환경과 같은지 비교합니다. "
                "`schema.뷰이름` 또는 `object_id`를 권장합니다."
            ),
            "table": (
                "첫 번째 열에 **테이블 이름**을 한 줄에 하나씩 넣습니다. "
                "각 환경에서 컬럼·타입·NULL·IDENTITY·계산열 정의 등 스키마 메타를 직렬화해 기준 환경과 비교합니다. "
                "`schema.테이블명` 또는 `object_id`를 권장합니다."
            ),
        }
        st.caption(
            f"위에서 고른 **[비교 대상 유형]**이 `{object_kind}` 일 때만 동작합니다. "
            f"{bulk_help[object_kind]} "
            "엑셀 첫 행은 열 제목(헤더)으로 두어도 됩니다. 비교할 DB에는 환경마다 연결을 한 번만 맺습니다."
        )
        uploaded = st.file_uploader("엑셀 파일", type=["xlsx", "xls"], key="bulk_excel_upload")
        if st.button("일괄 비교 실행", type="primary", key="bulk_compare_run"):
            if baseline not in envs:
                st.error("기준 환경은 비교 환경 목록에 포함되어야 합니다.")
            elif uploaded is None:
                st.error("엑셀 파일을 업로드하세요.")
            else:
                bulk_kind: ObjectKind = cast(ObjectKind, object_kind)
                try:
                    df = _read_bulk_excel_first_sheet(uploaded)
                    identifiers = _first_column_identifiers(df)
                except Exception as exc:
                    st.error(f"엑셀을 읽지 못했습니다: {exc}")
                else:
                    if not identifiers:
                        st.error("첫 번째 열에서 비교할 값이 없습니다.")
                    else:
                        with st.spinner("일괄 비교 중입니다..."):
                            try:
                                configs = _load_configs(envs)
                            except Exception as exc:
                                st.error(f"환경 설정 오류: {exc}")
                            else:
                                results: List[Dict[str, object]] = []
                                definitions_map: Dict[str, Dict[str, object]] = {}
                                errors: Dict[str, str] = {}
                                conns: Dict[str, pyodbc.Connection] = {}
                                try:
                                    for cfg in configs:
                                        conns[cfg.name] = open_connection(cfg)

                                    many: Dict[str, Dict[str, object]] | None = None
                                    if bulk_kind in ("routine", "view"):
                                        many = compare_many_across_envs_by_object_id(
                                            configs,
                                            identifiers,
                                            object_kind=bulk_kind,
                                            connections=conns,
                                        )
                                        if many is None:
                                            many = compare_many_across_envs_by_qualified_module_name(
                                                configs,
                                                identifiers,
                                                object_kind=bulk_kind,
                                                connections=conns,
                                            )
                                    else:
                                        many = compare_many_across_envs_by_object_id(
                                            configs,
                                            identifiers,
                                            object_kind="table",
                                            connections=conns,
                                        )
                                        if many is None:
                                            many = compare_many_across_envs_by_qualified_table_name(
                                                configs,
                                                identifiers,
                                                connections=conns,
                                            )

                                    for ident in identifiers:
                                        try:
                                            if many is not None and ident in many:
                                                definitions = many[ident]
                                            else:
                                                definitions = compare_across_envs(
                                                    configs,
                                                    ident,
                                                    object_kind=bulk_kind,
                                                    connections=conns,
                                                )
                                            definitions_map[ident] = definitions
                                            base_def = definitions[baseline]
                                            row: Dict[str, object] = {"대상": ident}
                                            any_diff = False
                                            for env_name, proc_def in definitions.items():
                                                status = "SAME" if proc_def.digest == base_def.digest else "DIFF"
                                                row[env_name] = status
                                                if status == "DIFF":
                                                    any_diff = True
                                            row["상태"] = "DIFF" if any_diff else "SAME"
                                            results.append(row)
                                        except Exception as exc:
                                            errors[ident] = str(exc)
                                            err_row: Dict[str, object] = {"대상": ident, "상태": "ERROR"}
                                            for env_name in envs:
                                                err_row[env_name] = "ERROR"
                                            results.append(err_row)
                                finally:
                                    for c in conns.values():
                                        try:
                                            c.close()
                                        except Exception:
                                            pass

                                st.session_state["bulk_results"] = results
                                st.session_state["bulk_definitions"] = definitions_map
                                st.session_state["bulk_errors"] = errors
                                st.session_state["bulk_object_kind"] = bulk_kind

        if st.session_state["bulk_results"]:
            st.subheader("결과 요약")
            st.dataframe(st.session_state["bulk_results"], use_container_width=True)
            if st.session_state["bulk_errors"]:
                st.warning("오류: " + ", ".join(st.session_state["bulk_errors"].keys()))
            opts = list(st.session_state["bulk_definitions"].keys())
            if opts:
                pick = st.selectbox("상세 비교할 대상", opts, key="bulk_detail_pick")
                if pick:
                    bk = cast(
                        ObjectKind,
                        st.session_state.get("bulk_object_kind", object_kind),
                    )
                    _render_results(
                        baseline,
                        st.session_state["bulk_definitions"][pick],
                        bk,
                        widget_scope="bulk_compare",
                    )

    with tabs[3]:
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


if __name__ == "__main__":
    main()
