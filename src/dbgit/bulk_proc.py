"""엑셀에서 읽은 식별자 목록에 대한 프로시저/함수 일괄 비교 (CLI·UI 공통 로직)."""

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from .compare import ProcDefinition, compare_across_envs
from .config import EnvConfig


def extract_proc_ids_from_excel(uploaded: object) -> List[str]:
    """엑셀 바이너리/UploadedFile. 우선 컬럼명 proc|procedure|object_id|name, 없으면 첫 열."""
    df = pd.read_excel(uploaded)
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


def bulk_compare_procedures(
    identifiers: List[str],
    configs: List[EnvConfig],
    baseline: str,
    envs: List[str],
) -> Tuple[List[Dict[str, object]], Dict[str, Dict[str, ProcDefinition]], Dict[str, str]]:
    """
    반환:
      rows — 테이블 행 리스트
      definitions_map — 성공한 식별자만, 환경명 -> ProcDefinition
      errors — 실패한 식별자 -> 메시지
    """
    results: List[Dict[str, object]] = []
    definitions_map: Dict[str, Dict[str, ProcDefinition]] = {}
    errors: Dict[str, str] = {}

    for identifier in identifiers:
        try:
            definitions = compare_across_envs(configs, identifier)
            definitions_map[identifier] = definitions
            base_def = definitions[baseline]
            row: Dict[str, object] = {"대상": identifier}
            any_diff = False
            for env_name, proc_def in definitions.items():
                status = "SAME" if proc_def.digest == base_def.digest else "DIFF"
                row[env_name] = status
                if status == "DIFF":
                    any_diff = True
            row["상태"] = "DIFF" if any_diff else "SAME"
            results.append(row)
        except Exception as exc:
            errors[identifier] = str(exc)
            row = {"대상": identifier, "상태": "ERROR"}
            for env_name in envs:
                row[env_name] = "ERROR"
            results.append(row)

    return results, definitions_map, errors
