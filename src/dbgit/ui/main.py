"""Streamlit 페이지 레이아웃·탭 조합."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from ..constants import DEFAULT_ENVS
from .tab_bulk import init_bulk_session_state, tab_bulk
from .tab_common_code import tab_common_code
from .tab_single import tab_single


def run_main() -> None:
    st.set_page_config(page_title="DB 프로시저 비교", layout="wide")
    st.title("DB 프로시저 형상 비교")
    st.info("프로시저/함수 object_id 또는 schema.name을 입력하세요.")

    init_bulk_session_state()

    dotenv_path = st.text_input("dotenv 경로", value=".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path, override=True)
    else:
        st.warning("dotenv 파일을 찾지 못했습니다. 환경변수가 직접 설정되어 있어야 합니다.")

    envs = st.multiselect("비교할 환경", DEFAULT_ENVS, default=DEFAULT_ENVS)
    baseline = st.selectbox("기준 환경", envs or DEFAULT_ENVS, index=0)

    tabs = st.tabs(["단일 비교", "엑셀 일괄 비교", "공통코드 비교"])
    with tabs[0]:
        tab_single(envs, baseline)
    with tabs[1]:
        tab_bulk(envs, baseline)
    with tabs[2]:
        tab_common_code(envs, baseline)
