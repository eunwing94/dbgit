"""엑셀 목록 기준 일괄 프로시저 비교."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from ..compare import ProcDefinition, compare_across_envs
from ..config import EnvConfig


@dataclass(frozen=True)
class BulkCompareOutcome:
    """일괄 비교 한 번 실행의 결과."""

    results: List[dict]
    definitions_map: Dict[str, Dict[str, ProcDefinition]]
    errors: Dict[str, str]


def run_bulk_compare(
    configs: List[EnvConfig],
    identifiers: List[str],
    baseline: str,
    envs: List[str],
) -> BulkCompareOutcome:
    """식별자마다 환경 전체 비교를 수행하고 요약 행·상세·오류를 반환합니다."""
    results: List[dict] = []
    definitions_map: Dict[str, Dict[str, ProcDefinition]] = {}
    errors: Dict[str, str] = {}

    for identifier in identifiers:
        try:
            definitions = compare_across_envs(configs, identifier)
            definitions_map[identifier] = definitions
            base_def = definitions[baseline]
            row: dict = {"대상": identifier}
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

    return BulkCompareOutcome(
        results=results,
        definitions_map=definitions_map,
        errors=errors,
    )
