"""Streamlit 앱 조립 및 실행."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from ..constants import DEFAULT_ENVS
from .state import init_session_state
from .tab_bulk import render_bulk_compare_tab
from .tab_common_code import render_common_code_tab
from .tab_pdf_unlock import render_pdf_unlock_tab
from .tab_single import render_single_compare_tab


def run_streamlit_app() -> None:
    st.set_page_config(page_title="DB 프로시저 비교", layout="wide")
    st.title("DB 프로시저 형상 비교")

    init_session_state()
    st.info("프로시저/함수 object_id 또는 schema.name을 입력하세요.")

    dotenv_path = st.text_input("dotenv 경로", value=".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path, override=True)
    else:
        st.warning("dotenv 파일을 찾지 못했습니다. 환경변수가 직접 설정되어 있어야 합니다.")

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
