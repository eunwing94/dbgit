from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import pandas as pd

from .config import EnvConfig
from .db import open_connection


KEY_COLS = ["COMP_CD", "CM_CD", "DTL_CD"]
VALUE_COLS = ["TSK_SE_CD", "DTL_CD_NM", "SORT_NO", "USE_YN"]
ALL_COLS = KEY_COLS + VALUE_COLS


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


def compare_cm_cd_d(
    configs: Iterable[EnvConfig],
    baseline: str,
) -> CommonCodeResult:
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
            row = {col: value for col, value in zip(KEY_COLS, key)}
            row["비교환경"] = env_name

            if key not in env_index:
                row["상태"] = "MISSING_IN_ENV"
                row["차이나는컬럼"] = "ALL"
                for col in VALUE_COLS:
                    row[f"BASE_{col}"] = base_df.loc[key, col]
                    row[f"{env_name}_{col}"] = ""
                rows.append(row)
                continue

            if key not in base_index:
                row["상태"] = "MISSING_IN_BASE"
                row["차이나는컬럼"] = "ALL"
                for col in VALUE_COLS:
                    row[f"BASE_{col}"] = ""
                    row[f"{env_name}_{col}"] = env_df.loc[key, col]
                rows.append(row)
                continue

            diff_cols = []
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

            rows.append(row)

    result_df = pd.DataFrame(rows)
    return CommonCodeResult(rows=result_df, source=env_map)
