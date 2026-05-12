"""PDF 암호 제거 탭."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ..pdf_unlock import PdfPasswordError, strip_pdf_encryption


def _safe_pdf_base_name(name: str | None) -> str:
    if not name or not str(name).strip():
        return "document"
    base = Path(str(name)).name
    if base.lower().endswith(".pdf"):
        base = base[:-4]
    return base or "document"


def render_pdf_unlock_tab() -> None:
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
