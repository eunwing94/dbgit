"""pandas DataFrame → xlsx 바이트 (공통코드 다운로드 등)."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def dataframe_to_xlsx_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    buffer.seek(0)
    return buffer.read()


def common_code_two_sheet_bytes(
    summary_df: pd.DataFrame,
    detail_df: pd.DataFrame,
    *,
    summary_sheet: str = "요약",
    detail_sheet: str = "상세",
) -> bytes:
    """요약 + 상세 두 시트를 한 파일로."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name=summary_sheet[:31])
        detail_df.to_excel(writer, index=False, sheet_name=detail_sheet[:31])
    buffer.seek(0)
    return buffer.read()


def stringify_sort_no_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Streamlit Arrow 직렬화 호환: SORT_NO 계열을 문자열로."""
    out = df.copy()
    for col in out.columns:
        if "SORT_NO" in str(col):
            out[col] = out[col].fillna("").astype(str)
    return out
