"""프로시저·함수 정의를 sys.sql_modules에서 읽어 환경 간 해시 비교."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Dict, Iterable

from .config import EnvConfig
from .db import fetch_one, open_connection

logger = logging.getLogger("dbgit.compare")


@dataclass(frozen=True)
class ProcDefinition:
    """단일 환경에서 조회한 객체 정의."""

    object_id: int
    schema_name: str
    name: str
    definition: str
    normalized_definition: str

    @property
    def full_name(self) -> str:
        """schema.object_name"""
        return f"{self.schema_name}.{self.name}"

    @property
    def digest(self) -> str:
        """정규화된 정의 본문의 SHA-256 (공백 무시 비교용)."""
        return hashlib.sha256(self.normalized_definition.encode("utf-8")).hexdigest()


# object_id(숫자) 또는 객체명/스키마.객체명으로 매칭
# type: P 프로시저, PC CLR 프로시저, FN/IF/TF 함수
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
    """숫자 문자열이면 object_id로 간주."""
    try:
        return int(proc_identifier)
    except ValueError:
        return None


def _normalize_definition(definition: str) -> str:
    """모든 공백 제거 후 비교 (포매팅 차이 무시)."""
    return re.sub(r"\s+", "", definition)


def fetch_proc_definition(config: EnvConfig, proc_identifier: str) -> ProcDefinition:
    """지정 환경에서 프로시저/함수 정의 1건 조회."""
    object_id = _parse_object_id(proc_identifier)
    logger.info("프로시저 조회 env=%s identifier=%s", config.name, proc_identifier)
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
    """모든 환경에 대해 동일 식별자로 정의를 가져온 딕셔너리."""
    logger.info("환경 간 비교 시작 identifier=%s", proc_identifier)
    results: Dict[str, ProcDefinition] = {}
    for config in configs:
        results[config.name] = fetch_proc_definition(config, proc_identifier)
    logger.info("환경 간 비교 완료 identifier=%s", proc_identifier)
    return results
