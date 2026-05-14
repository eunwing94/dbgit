"""Streamlit 앱 조립 및 실행."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from ..constants import DEFAULT_ENVS
from .state import init_session_state
from .tab_bulk import render_bulk_compare_tab
from .tab_common_code import render_common_code_tab
from .tab_pdf_unlock import render_pdf_unlock_tab
from .tab_single import render_single_compare_tab

# src/dbgit/ui/main.py → 저장소 루트
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve_dotenv_path(user_path: str) -> Path:
    """실행 cwd와 무관하게 프로젝트 루트 기준으로 경로를 잡습니다."""
    p = Path(user_path.strip() or ".env")
    if not p.is_absolute():
        p = (PROJECT_ROOT / p).resolve()
    return p


def run_streamlit_app() -> None:
    st.set_page_config(page_title="DB 프로시저 비교", layout="wide")
    st.title("DB 프로시저 형상 비교")

    init_session_state()
    st.info("프로시저/함수 object_id 또는 schema.name을 입력하세요.")

    dotenv_path = st.text_input(
        "dotenv 경로",
        value=".env",
        help="프로젝트 루트 기준 상대 경로이거나, 절대 경로를 넣을 수 있습니다.",
    )
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
                "샘플: 터미널에서 프로젝트 루트로 이동한 뒤 `cp .env.example .env` 후 `.env`를 편집하세요."
            )
        lines.append(
            "이미 터미널·IDE·OS에 동일 이름의 환경변수를 넣었다면 `.env` 없이도 동작할 수 있습니다."
        )
        st.info(" ".join(lines))

    envs = st.multiselect("비교할 환경", DEFAULT_ENVS, default=DEFAULT_ENVS)
    baseline = st.selectbox("기준 환경", envs or DEFAULT_ENVS, index=0)

    tabs = st.tabs(["단일 비교", "엑셀 일괄 비교", "공통코드 비교", "PDF 암호 제거"])

    with tabs[0]:
        render_single_compare_tab(envs, baseline)
    with tabs[1]:
        render_bulk_compare_tab(envs, baseline)
    with tabs[2]:
        render_common_code_tab(envs, baseline)
    with tabs[3]:
        render_pdf_unlock_tab()
