from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, Literal

import pyodbc

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


def _parse_object_id_loose(text: str) -> int | None:
    """엑셀 등에서 온 문자열을 object_id로 해석 (정수, 또는 12345.0 형태의 실수)."""
    t = (text or "").strip()
    if not t:
        return None
    try:
        return int(t)
    except ValueError:
        pass
    try:
        f = float(t)
        if f != f:  # NaN
            return None
        i = int(f)
        if abs(f - float(i)) > 1e-9:
            return None
        return i
    except (ValueError, OverflowError):
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
    *,
    conn: pyodbc.Connection | None = None,
) -> ProcDefinition:
    object_id = _parse_object_id(proc_identifier)
    placeholders = _format_sql_type_placeholders(object_types)
    query = ROUTINE_OR_VIEW_QUERY.format(type_placeholders=placeholders)
    params: tuple[object, ...] = (*object_types, object_id, proc_identifier, proc_identifier, object_id)
    if conn is not None:
        cursor = conn.cursor()
        row = fetch_one(cursor, query, params)
    else:
        with open_connection(config) as managed:
            cursor = managed.cursor()
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


def fetch_proc_definition(
    config: EnvConfig,
    proc_identifier: str,
    *,
    conn: pyodbc.Connection | None = None,
) -> ProcDefinition:
    """프로시저·함수 (P, PC, FN, IF, TF). `conn`이 있으면 새 연결을 열지 않고 해당 연결을 사용합니다."""
    return _fetch_sql_module_object(
        config,
        proc_identifier,
        ROUTINE_TYPES,
        "프로시저/함수를 찾지 못했습니다",
        conn=conn,
    )


def fetch_view_definition(
    config: EnvConfig,
    identifier: str,
    *,
    conn: pyodbc.Connection | None = None,
) -> ProcDefinition:
    """뷰 (V) — sys.sql_modules 정의 텍스트 기준."""
    return _fetch_sql_module_object(
        config,
        identifier,
        ("V",),
        "뷰를 찾지 못했습니다",
        conn=conn,
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


def _row_to_proc_definition_sql_module(row: object) -> ProcDefinition:
    definition = row.definition or ""
    normalized = _normalize_definition(definition)
    return ProcDefinition(
        object_id=int(row.object_id),
        schema_name=row.schema_name,
        name=row.name,
        definition=definition,
        normalized_definition=normalized,
    )


def _fetch_many_sql_module_by_object_ids(
    object_types: tuple[str, ...],
    object_ids: list[int],
    conn: pyodbc.Connection,
) -> dict[int, ProcDefinition]:
    """한 환경에서 object_id IN (...) 으로 여러 모듈 정의를 한 번에 조회합니다."""
    if not object_ids:
        return {}
    type_ph = _format_sql_type_placeholders(object_types)
    id_ph = ", ".join("?" * len(object_ids))
    query = f"""
SELECT
    o.object_id,
    s.name AS schema_name,
    o.name,
    m.definition
FROM sys.objects o
INNER JOIN sys.sql_modules m ON m.object_id = o.object_id
INNER JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE o.type IN ({type_ph})
  AND o.object_id IN ({id_ph})
"""
    params: tuple[object, ...] = (*object_types, *object_ids)
    cursor = conn.cursor()
    rows = fetch_all(cursor, query, params)
    return {int(r.object_id): _row_to_proc_definition_sql_module(r) for r in rows}


def _fetch_many_tables_by_object_ids(
    object_ids: list[int],
    conn: pyodbc.Connection,
) -> dict[int, ProcDefinition]:
    """한 환경에서 여러 테이블(U)의 컬럼 스키마를 IN 쿼리로 묶어 조회합니다."""
    if not object_ids:
        return {}
    id_ph = ", ".join("?" * len(object_ids))
    params_tuple = tuple(object_ids)
    meta_sql = f"""
SELECT o.object_id, s.name AS schema_name, o.name
FROM sys.objects o
INNER JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE o.type = N'U'
  AND o.object_id IN ({id_ph})
"""
    cursor = conn.cursor()
    meta_rows = fetch_all(cursor, meta_sql, params_tuple)
    metas = {int(r.object_id): r for r in meta_rows}

    col_sql = f"""
SELECT
    c.object_id,
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
WHERE c.object_id IN ({id_ph})
ORDER BY c.object_id, c.column_id
"""
    col_rows = fetch_all(cursor, col_sql, params_tuple)
    cols_by_oid: dict[int, list[object]] = defaultdict(list)
    for r in col_rows:
        cols_by_oid[int(r.object_id)].append(r)

    out: dict[int, ProcDefinition] = {}
    for oid, meta in metas.items():
        rows = cols_by_oid.get(oid, [])
        blob = table_schema_text_from_rows(rows)
        normalized = _normalize_definition(blob)
        out[oid] = ProcDefinition(
            object_id=int(meta.object_id),
            schema_name=meta.schema_name,
            name=meta.name,
            definition=blob,
            normalized_definition=normalized,
        )
    return out


def compare_many_across_envs_by_object_id(
    configs: Iterable[EnvConfig],
    identifiers: list[str],
    *,
    object_kind: ObjectKind,
    connections: Dict[str, pyodbc.Connection],
) -> Dict[str, Dict[str, ProcDefinition]] | None:
    """
    모든 식별자가 object_id로 해석되면, 환경당 1~2회 쿼리로 일괄 조회합니다.
    그렇지 않으면 None (호출부에서 건별 compare_across_envs 사용).
    일부 환경에만 객체가 없으면 해당 행만 건별 조회로 보완합니다.
    """
    kind: ObjectKind = object_kind  # type: ignore[assignment]
    if kind not in ("routine", "view", "table"):
        raise ValueError(f"지원하지 않는 object_kind: {object_kind}")

    pairs: list[tuple[str, int]] = []
    for raw in identifiers:
        s = raw.strip()
        oid = _parse_object_id_loose(s)
        if oid is None:
            return None
        pairs.append((s, oid))

    configs_list = list(configs)
    unique_oids = sorted(set(oid for _, oid in pairs))

    by_env: dict[str, dict[int, ProcDefinition]] = {}
    for config in configs_list:
        conn = connections[config.name]
        if kind == "routine":
            by_env[config.name] = _fetch_many_sql_module_by_object_ids(
                ROUTINE_TYPES, unique_oids, conn
            )
        elif kind == "view":
            by_env[config.name] = _fetch_many_sql_module_by_object_ids(
                ("V",), unique_oids, conn
            )
        else:
            by_env[config.name] = _fetch_many_tables_by_object_ids(unique_oids, conn)

    out: dict[str, Dict[str, ProcDefinition]] = {}
    for ident_s, oid in pairs:
        use_batch = all(oid in by_env[c.name] for c in configs_list)
        if use_batch:
            out[ident_s] = {c.name: by_env[c.name][oid] for c in configs_list}
        else:
            out[ident_s] = compare_across_envs(
                configs_list,
                str(oid),
                object_kind=kind,
                connections=connections,
            )
    return out


def _norm_module_full_name(s: str) -> str:
    return s.strip().lower()


def _fetch_many_sql_module_by_full_names_lowered(
    object_types: tuple[str, ...],
    lowered_full_names: list[str],
    conn: pyodbc.Connection,
) -> dict[str, ProcDefinition]:
    """키: LOWER(schema.name) — 한 환경에서 여러 qualified name을 IN 한 번으로 조회."""
    if not lowered_full_names:
        return {}
    type_ph = _format_sql_type_placeholders(object_types)
    name_ph = ", ".join("?" * len(lowered_full_names))
    query = f"""
SELECT
    o.object_id,
    s.name AS schema_name,
    o.name,
    m.definition
FROM sys.objects o
INNER JOIN sys.sql_modules m ON m.object_id = o.object_id
INNER JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE o.type IN ({type_ph})
  AND LOWER(s.name + N'.' + o.name) IN ({name_ph})
"""
    params: tuple[object, ...] = (*object_types, *lowered_full_names)
    cursor = conn.cursor()
    rows = fetch_all(cursor, query, params)
    out: dict[str, ProcDefinition] = {}
    for r in rows:
        k = _norm_module_full_name(f"{r.schema_name}.{r.name}")
        out[k] = _row_to_proc_definition_sql_module(r)
    return out


def compare_many_across_envs_by_qualified_module_name(
    configs: Iterable[EnvConfig],
    identifiers: list[str],
    *,
    object_kind: ObjectKind,
    connections: Dict[str, pyodbc.Connection],
) -> Dict[str, Dict[str, ProcDefinition]] | None:
    """
    routine / view 이고, 모든 식별자가 `schema.object` 형태(점 포함)이면
    환경당 한 번의 IN 쿼리로 일괄 조회합니다. table 이거나 점 없는 이름이 섞이면 None.
    """
    kind: ObjectKind = object_kind  # type: ignore[assignment]
    if kind not in ("routine", "view"):
        return None

    stripped: list[str] = []
    for raw in identifiers:
        s = raw.strip()
        if not s or "." not in s:
            return None
        stripped.append(s)

    configs_list = list(configs)
    unique_lowered = sorted({_norm_module_full_name(x) for x in stripped})

    object_types: tuple[str, ...] = ROUTINE_TYPES if kind == "routine" else ("V",)

    by_env: dict[str, dict[str, ProcDefinition]] = {}
    for config in configs_list:
        conn = connections[config.name]
        by_env[config.name] = _fetch_many_sql_module_by_full_names_lowered(
            object_types, unique_lowered, conn
        )

    out: dict[str, Dict[str, ProcDefinition]] = {}
    for ident_s in stripped:
        n = _norm_module_full_name(ident_s)
        use_batch = all(n in by_env[c.name] for c in configs_list)
        if use_batch:
            out[ident_s] = {c.name: by_env[c.name][n] for c in configs_list}
        else:
            out[ident_s] = compare_across_envs(
                configs_list,
                ident_s,
                object_kind=kind,
                connections=connections,
            )
    return out


def _fetch_many_tables_by_qualified_names_lowered(
    lowered_full_names: list[str],
    conn: pyodbc.Connection,
) -> dict[str, ProcDefinition]:
    """키: LOWER(schema.table) — 사용자 테이블(U) 여러 개를 메타·컬럼 IN 쿼리로 묶어 조회."""
    if not lowered_full_names:
        return {}
    name_ph = ", ".join("?" * len(lowered_full_names))
    params_meta = tuple(lowered_full_names)
    meta_sql = f"""
SELECT o.object_id, s.name AS schema_name, o.name
FROM sys.objects o
INNER JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE o.type = N'U'
  AND LOWER(s.name + N'.' + o.name) IN ({name_ph})
"""
    cursor = conn.cursor()
    meta_rows = fetch_all(cursor, meta_sql, params_meta)
    if not meta_rows:
        return {}
    oids = sorted({int(r.object_id) for r in meta_rows})
    id_ph = ", ".join("?" * len(oids))
    col_sql = f"""
SELECT
    c.object_id,
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
WHERE c.object_id IN ({id_ph})
ORDER BY c.object_id, c.column_id
"""
    col_rows = fetch_all(cursor, col_sql, tuple(oids))
    cols_by_oid: dict[int, list[object]] = defaultdict(list)
    for r in col_rows:
        cols_by_oid[int(r.object_id)].append(r)

    out: dict[str, ProcDefinition] = {}
    for meta in meta_rows:
        oid = int(meta.object_id)
        rows = cols_by_oid.get(oid, [])
        blob = table_schema_text_from_rows(rows)
        normalized = _normalize_definition(blob)
        k = _norm_module_full_name(f"{meta.schema_name}.{meta.name}")
        out[k] = ProcDefinition(
            object_id=oid,
            schema_name=meta.schema_name,
            name=meta.name,
            definition=blob,
            normalized_definition=normalized,
        )
    return out


def compare_many_across_envs_by_qualified_table_name(
    configs: Iterable[EnvConfig],
    identifiers: list[str],
    *,
    connections: Dict[str, pyodbc.Connection],
) -> Dict[str, Dict[str, ProcDefinition]] | None:
    """
    모든 식별자가 `schema.table` 형태(점 포함)이면 환경당 IN 한 번으로 테이블 스키마를 일괄 조회합니다.
    """
    for raw in identifiers:
        s = raw.strip()
        if not s or "." not in s:
            return None
    stripped = [raw.strip() for raw in identifiers]
    configs_list = list(configs)
    unique_lowered = sorted({_norm_module_full_name(x) for x in stripped})

    by_env: dict[str, dict[str, ProcDefinition]] = {}
    for config in configs_list:
        conn = connections[config.name]
        by_env[config.name] = _fetch_many_tables_by_qualified_names_lowered(unique_lowered, conn)

    out: dict[str, Dict[str, ProcDefinition]] = {}
    for ident_s in stripped:
        n = _norm_module_full_name(ident_s)
        use_batch = all(n in by_env[c.name] for c in configs_list)
        if use_batch:
            out[ident_s] = {c.name: by_env[c.name][n] for c in configs_list}
        else:
            out[ident_s] = compare_across_envs(
                configs_list,
                ident_s,
                object_kind="table",
                connections=connections,
            )
    return out


def fetch_table_schema_definition(
    config: EnvConfig,
    identifier: str,
    *,
    conn: pyodbc.Connection | None = None,
) -> ProcDefinition:
    """사용자 테이블(U) — 컬럼·타입·NULL 등 메타를 직렬화해 환경 간 스키마 갭을 비교합니다."""
    object_id = _parse_object_id(identifier)

    def _run_queries(cursor: pyodbc.Cursor) -> tuple[object, list[object]]:
        meta = fetch_one(
            cursor,
            TABLE_OBJECT_QUERY,
            (object_id, identifier, identifier, object_id),
        )
        if meta is None:
            raise ValueError(f"{config.name}에서 테이블을 찾지 못했습니다: {identifier}")
        rows = fetch_all(cursor, TABLE_COLUMNS_QUERY, (meta.object_id,))
        return meta, rows

    if conn is not None:
        cursor = conn.cursor()
        meta, rows = _run_queries(cursor)
    else:
        with open_connection(config) as managed:
            cursor = managed.cursor()
            meta, rows = _run_queries(cursor)

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
    connections: Dict[str, pyodbc.Connection] | None = None,
) -> Dict[str, ProcDefinition]:
    """
    object_kind에 따라 프로시저·함수 / 뷰 / 테이블(스키마)을 환경별로 조회합니다.

    `connections`에 환경 이름 → 열린 `pyodbc` 연결을 넘기면 해당 연결을 재사용합니다.
    (일괄 비교 등에서 연결마다 핸드셰이크 비용을 줄이기 위함.)
    """
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
        c = connections.get(config.name) if connections else None
        results[config.name] = fetch(config, proc_identifier, conn=c)
    return results
