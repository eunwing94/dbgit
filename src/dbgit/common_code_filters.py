"""공통코드 비교 결과 DataFrame 필터 (UI·엑셀 내보내기 전처리)."""

from __future__ import annotations

import pandas as pd


def filter_common_code_df(
    df: pd.DataFrame,
    *,
    hide_same: bool = False,
    comp_cd_prefix: str = "",
    cm_cd_prefix: str = "",
) -> pd.DataFrame:
    """
    - hide_same: 상태 열이 SAME인 행 제거
    - comp_cd_prefix / cm_cd_prefix: 각각 해당 컬럼 접두어로 시작하는 행만 (대소문자 구분 없음)
    """
    out = df.copy()
    if hide_same and "상태" in out.columns:
        out = out[out["상태"].astype(str) != "SAME"]
    p_comp = comp_cd_prefix.strip()
    p_cm = cm_cd_prefix.strip()
    if p_comp and "COMP_CD" in out.columns:
        out = out[out["COMP_CD"].astype(str).str.upper().str.startswith(p_comp.upper())]
    if p_cm and "CM_CD" in out.columns:
        out = out[out["CM_CD"].astype(str).str.upper().str.startswith(p_cm.upper())]
    return out.reset_index(drop=True)


def build_common_code_summary(detail_df: pd.DataFrame) -> pd.DataFrame:
    """요약 시트: 비교환경·상태별 건수."""
    if detail_df.empty:
        return pd.DataFrame(columns=["비교환경", "상태", "건수"])
    cols = [c for c in ("비교환경", "상태") if c in detail_df.columns]
    if len(cols) < 2:
        return pd.DataFrame({"메시지": ["비교환경/상태 열이 없어 요약을 만들 수 없습니다."]})
    g = (
        detail_df.groupby(cols, dropna=False)
        .size()
        .reset_index(name="건수")
        .sort_values(cols)
    )
    return g
