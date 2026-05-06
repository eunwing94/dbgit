"""CM_CD_D(+ CM_CD_M 조인) 공통코드를 환경별로 읽고 기준 환경 대비 갭을 산출."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

from .config import EnvConfig
from .db import open_connection

logger = logging.getLogger("dbgit.common_code")

KEY_COLS = ["COMP_CD", "CM_CD", "DTL_CD"]
VALUE_COLS = ["TSK_SE_CD", "DTL_CD_NM", "SORT_NO", "USE_YN"]

@dataclass(frozen=True)
class CommonCodeResult:
    rows: pd.DataFrame
    source: Dict[str, pd.DataFrame]


def _normalize_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["COMP_CD", "CM_CD", "DTL_CD", "TSK_SE_CD", "DTL_CD_NM", "USE_YN"]:
        df[col] = _normalize_text(df[col])
    df["SORT_NO"] = pd.to_numeric(df["SORT_NO"], errors="coerce")
    return df


def fetch_cm_cd_d(config: EnvConfig) -> pd.DataFrame:
    query = """
    SELECT
        d.COMP_CD,
        d.CM_CD,
        d.DTL_CD,
        m.TSK_SE_CD,
        d.DTL_CD_NM,
        d.SORT_NO,
        d.USE_YN
    FROM CM_CD_D d
    LEFT JOIN CM_CD_M m
        ON d.COMP_CD = m.COMP_CD
       AND d.CM_CD = m.CM_CD
    """
    with open_connection(config) as conn:
        df = pd.read_sql_query(query, conn)
    return _normalize_dataframe(df)


def _key_dict(key: Tuple[Any, ...]) -> Dict[str, object]:
    return dict(zip(KEY_COLS, key))


def _row_missing_in_env(
    key: Tuple[Any, ...],
    env_name: str,
    base_df: pd.DataFrame,
) -> Dict[str, object]:
    row: Dict[str, object] = _key_dict(key)
    row["비교환경"] = env_name
    row["상태"] = "MISSING_IN_ENV"
    row["차이나는컬럼"] = "ALL"
    for col in VALUE_COLS:
        row[f"BASE_{col}"] = base_df.loc[key, col]
        row[f"{env_name}_{col}"] = ""
    return row


def _row_missing_in_base(
    key: Tuple[Any, ...],
    env_name: str,
    env_df: pd.DataFrame,
) -> Dict[str, object]:
    row = _key_dict(key)
    row["비교환경"] = env_name
    row["상태"] = "MISSING_IN_BASE"
    row["차이나는컬럼"] = "ALL"
    for col in VALUE_COLS:
        row[f"BASE_{col}"] = ""
        row[f"{env_name}_{col}"] = env_df.loc[key, col]
    return row


def _row_both_sides(
    key: Tuple[Any, ...],
    env_name: str,
    base_df: pd.DataFrame,
    env_df: pd.DataFrame,
) -> Dict[str, object]:
    row = _key_dict(key)
    row["비교환경"] = env_name
    diff_cols: List[str] = []
    for col in VALUE_COLS:
        base_val = base_df.loc[key, col]
        env_val = env_df.loc[key, col]
        row[f"BASE_{col}"] = base_val
        row[f"{env_name}_{col}"] = env_val
        if pd.isna(base_val) and pd.isna(env_val):
            continue
        if base_val != env_val:
            diff_cols.append(col)
    if diff_cols:
        row["상태"] = "DIFF"
        row["차이나는컬럼"] = ", ".join(diff_cols)
    else:
        row["상태"] = "SAME"
        row["차이나는컬럼"] = ""
    return row


def compare_cm_cd_d(
    configs: Iterable[EnvConfig],
    baseline: str,
) -> CommonCodeResult:
    logger.info("공통코드 CM_CD_D 비교 시작 baseline=%s", baseline)
    env_map: Dict[str, pd.DataFrame] = {
        config.name: fetch_cm_cd_d(config) for config in configs
    }

    base_df = env_map[baseline].set_index(KEY_COLS)
    rows: List[Dict[str, object]] = []

    for env_name, env_df_raw in env_map.items():
        if env_name == baseline:
            continue
        env_df = env_df_raw.set_index(KEY_COLS)
        base_index = base_df.index
        env_index = env_df.index
        all_keys = base_index.union(env_index)

        for key in all_keys:
            if key not in env_index:
                rows.append(_row_missing_in_env(key, env_name, base_df))
                continue
            if key not in base_index:
                rows.append(_row_missing_in_base(key, env_name, env_df))
                continue
            rows.append(_row_both_sides(key, env_name, base_df, env_df))

    result = CommonCodeResult(rows=pd.DataFrame(rows), source=env_map)
    logger.info(
        "공통코드 비교 완료 baseline=%s 결과행수=%s",
        baseline,
        len(result.rows.index),
    )
    return result
