from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, Iterable, Literal

from .config import EnvConfig
from .db import fetch_all, fetch_one, open_connection

ObjectKind = Literal["routine", "view", "table"]


@dataclass(frozen=True)
class ProcDefinition:
    """비교 대상 객체(프로시저·함수·뷰·테이블 스키마)의 한 환경 스냅샷."""

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


ROUTINE_TYPES = ("P", "PC", "FN", "IF", "TF")

ROUTINE_OR_VIEW_QUERY = """
SELECT TOP 1
    o.object_id,
    s.name AS schema_name,
    o.name,
    m.definition
FROM sys.objects o
JOIN sys.sql_modules m ON o.object_id = m.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE o.type IN ({type_placeholders})
  AND (
        o.object_id = ?
        OR o.name = ?
        OR s.name + '.' + o.name = ?
  )
ORDER BY
    CASE WHEN o.object_id = ? THEN 0 ELSE 1 END,
    o.name;
"""

TABLE_OBJECT_QUERY = """
SELECT TOP 1
    o.object_id,
    s.name AS schema_name,
    o.name
FROM sys.objects o
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE o.type IN ('U')
  AND (
        o.object_id = ?
        OR o.name = ?
        OR s.name + '.' + o.name = ?
  )
ORDER BY
    CASE WHEN o.object_id = ? THEN 0 ELSE 1 END,
    o.name;
"""

TABLE_COLUMNS_QUERY = """
SELECT
    c.column_id,
    c.name AS column_name,
    ty.name AS type_name,
    c.max_length,
    c.precision,
    c.scale,
    c.is_nullable,
    c.is_identity,
    c.is_computed,
    ISNULL(cc.definition, N'') AS computed_definition
FROM sys.columns c
INNER JOIN sys.types ty ON ty.user_type_id = c.user_type_id
LEFT JOIN sys.computed_columns cc
    ON cc.object_id = c.object_id AND cc.column_id = c.column_id
WHERE c.object_id = ?
ORDER BY c.column_id;
"""


def _parse_object_id(proc_identifier: str) -> int | None:
    try:
        return int(proc_identifier)
    except ValueError:
        return None


def _normalize_definition(definition: str) -> str:
    return re.sub(r"\s+", "", definition)


def _format_sql_type_placeholders(types: tuple[str, ...]) -> str:
    return ", ".join("?" * len(types))


def _fetch_sql_module_object(
    config: EnvConfig,
    proc_identifier: str,
    object_types: tuple[str, ...],
    not_found_msg: str,
) -> ProcDefinition:
    object_id = _parse_object_id(proc_identifier)
    placeholders = _format_sql_type_placeholders(object_types)
    query = ROUTINE_OR_VIEW_QUERY.format(type_placeholders=placeholders)
    params: tuple[object, ...] = (*object_types, object_id, proc_identifier, proc_identifier, object_id)
    with open_connection(config) as conn:
        cursor = conn.cursor()
        row = fetch_one(cursor, query, params)

    if row is None:
        raise ValueError(f"{config.name}에서 {not_found_msg}: {proc_identifier}")

    definition = row.definition or ""
    normalized = _normalize_definition(definition)
    return ProcDefinition(
        object_id=row.object_id,
        schema_name=row.schema_name,
        name=row.name,
        definition=definition,
        normalized_definition=normalized,
    )


def fetch_proc_definition(config: EnvConfig, proc_identifier: str) -> ProcDefinition:
    """프로시저·함수 (P, PC, FN, IF, TF)."""
    return _fetch_sql_module_object(
        config,
        proc_identifier,
        ROUTINE_TYPES,
        "프로시저/함수를 찾지 못했습니다",
    )


def fetch_view_definition(config: EnvConfig, identifier: str) -> ProcDefinition:
    """뷰 (V) — sys.sql_modules 정의 텍스트 기준."""
    return _fetch_sql_module_object(
        config,
        identifier,
        ("V",),
        "뷰를 찾지 못했습니다",
    )


def _serialize_table_column_row(row: object) -> str:
    """컬럼 한 줄을 안정적인 구분 문자열로 직렬화 (해시·diff용)."""
    computed = getattr(row, "computed_definition", "") or ""
    computed_norm = _normalize_definition(str(computed).strip())
    parts = [
        str(int(row.column_id)),
        str(row.column_name),
        str(row.type_name),
        str(int(row.max_length)),
        str(int(row.precision)),
        str(int(row.scale)),
        "1" if bool(row.is_nullable) else "0",
        "1" if bool(row.is_identity) else "0",
        "1" if bool(row.is_computed) else "0",
        computed_norm,
    ]
    return "|".join(parts)


def table_schema_text_from_rows(rows: list[object]) -> str:
    """테스트·재사용용: 컬럼 row 목록을 정렬된 멀티라인 텍스트로."""
    return "\n".join(_serialize_table_column_row(r) for r in rows)


def fetch_table_schema_definition(config: EnvConfig, identifier: str) -> ProcDefinition:
    """사용자 테이블(U) — 컬럼·타입·NULL 등 메타를 직렬화해 환경 간 스키마 갭을 비교합니다."""
    object_id = _parse_object_id(identifier)
    with open_connection(config) as conn:
        cursor = conn.cursor()
        meta = fetch_one(
            cursor,
            TABLE_OBJECT_QUERY,
            (object_id, identifier, identifier, object_id),
        )
        if meta is None:
            raise ValueError(f"{config.name}에서 테이블을 찾지 못했습니다: {identifier}")

        rows = fetch_all(cursor, TABLE_COLUMNS_QUERY, (meta.object_id,))

    blob = table_schema_text_from_rows(rows)
    normalized = _normalize_definition(blob)
    return ProcDefinition(
        object_id=meta.object_id,
        schema_name=meta.schema_name,
        name=meta.name,
        definition=blob,
        normalized_definition=normalized,
    )


def compare_across_envs(
    configs: Iterable[EnvConfig],
    proc_identifier: str,
    *,
    object_kind: ObjectKind = "routine",
) -> Dict[str, ProcDefinition]:
    """object_kind에 따라 프로시저·함수 / 뷰 / 테이블(스키마)을 환경별로 조회합니다."""
    kind: ObjectKind = object_kind  # type: ignore[assignment]
    if kind not in ("routine", "view", "table"):
        raise ValueError(f"지원하지 않는 object_kind: {object_kind}")

    fetchers = {
        "routine": fetch_proc_definition,
        "view": fetch_view_definition,
        "table": fetch_table_schema_definition,
    }
    fetch = fetchers[kind]

    results: Dict[str, ProcDefinition] = {}
    for config in configs:
        results[config.name] = fetch(config, proc_identifier)
    return results
