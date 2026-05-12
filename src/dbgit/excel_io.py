"""엑셀 업로드·보내기 헬퍼."""

from __future__ import annotations

from io import BytesIO
from typing import List

import pandas as pd


def extract_proc_ids_from_excel(uploaded_file: object) -> List[str]:
    """엑셀에서 프로시저 식별자 목록을 추출합니다."""
    df = pd.read_excel(uploaded_file)
    if df.empty:
        return []
    for candidate in ("proc", "procedure", "object_id", "name"):
        if candidate in df.columns:
            series = df[candidate]
            break
    else:
        series = df.iloc[:, 0]
    values: List[str] = []
    for item in series.tolist():
        if item is None or (isinstance(item, float) and pd.isna(item)):
            continue
        text = str(item).strip()
        if text:
            values.append(text)
    return values


def build_cm_cd_d_excel_bytes(result_df: pd.DataFrame) -> bytes:
    """공통코드 비교 결과를 xlsx 바이트로 직렬화합니다."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False, sheet_name="CM_CD_D_DIFF")
    buffer.seek(0)
    return buffer.read()
