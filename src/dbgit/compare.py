from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, Iterable

from .config import EnvConfig
from .db import fetch_one, open_connection


@dataclass(frozen=True)
class ProcDefinition:
    object_id: int
    schema_name: str
    name: str
    definition: str
    normalized_definition: str

    @property
    def full_name(self) -> str:
        return f"{self.schema_name}.{self.name}"

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.normalized_definition.encode("utf-8")).hexdigest()


SUPPORTED_TYPES = ("P", "PC", "FN", "IF", "TF")

PROC_QUERY = """
SELECT TOP 1
    o.object_id,
    s.name AS schema_name,
    o.name,
    m.definition
FROM sys.objects o
JOIN sys.sql_modules m ON o.object_id = m.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE o.type IN ('P', 'PC', 'FN', 'IF', 'TF')
  AND (
        o.object_id = ?
        OR o.name = ?
        OR s.name + '.' + o.name = ?
  )
ORDER BY
    CASE WHEN o.object_id = ? THEN 0 ELSE 1 END,
    o.name;
"""


def _parse_object_id(proc_identifier: str) -> int | None:
    try:
        return int(proc_identifier)
    except ValueError:
        return None


def _normalize_definition(definition: str) -> str:
    # 공백/개행 차이는 비교에서 제외
    return re.sub(r"\s+", "", definition)


def fetch_proc_definition(config: EnvConfig, proc_identifier: str) -> ProcDefinition:
    object_id = _parse_object_id(proc_identifier)
    with open_connection(config) as conn:
        cursor = conn.cursor()
        row = fetch_one(
            cursor,
            PROC_QUERY,
            (
                object_id,
                proc_identifier,
                proc_identifier,
                object_id,
            ),
        )

    if row is None:
        raise ValueError(f"{config.name}에서 프로시저를 찾지 못했습니다: {proc_identifier}")

    definition = row.definition or ""
    normalized = _normalize_definition(definition)
    return ProcDefinition(
        object_id=row.object_id,
        schema_name=row.schema_name,
        name=row.name,
        definition=definition,
        normalized_definition=normalized,
    )


def compare_across_envs(
    configs: Iterable[EnvConfig],
    proc_identifier: str,
) -> Dict[str, ProcDefinition]:
    results: Dict[str, ProcDefinition] = {}
    for config in configs:
        results[config.name] = fetch_proc_definition(config, proc_identifier)
    return results
