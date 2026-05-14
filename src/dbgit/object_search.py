"""기준 DB에서 프로시저·함수·뷰·테이블을 이름/본문(정의) 조건으로 검색."""

from __future__ import annotations

from dataclasses import dataclass

from .compare import ROUTINE_TYPES, ObjectKind
from .config import EnvConfig
from .db import fetch_all, open_connection


@dataclass(frozen=True)
class ObjectSearchHit:
    """검색 결과 한 행."""

    schema_name: str
    name: str
    object_id: int
    sql_type: str
    compare_kind: ObjectKind

    @property
    def full_name(self) -> str:
        return f"{self.schema_name}.{self.name}"


def escape_sql_like_fragment(fragment: str) -> str:
    """LIKE 패턴에 삽입할 문자열에서 %, _, [ 를 이스케이프합니다."""
    return fragment.replace("[", "[[]").replace("%", "[%]").replace("_", "[_]")


def build_contains_pattern(needle: str) -> str:
    """SQL LIKE '%...%' 용 패턴 (공백만 있는 입력은 허용하지 않음)."""
    stripped = needle.strip()
    if not stripped:
        return ""
    return f"%{escape_sql_like_fragment(stripped)}%"


def _sql_type_to_compare_kind(sql_type: str) -> ObjectKind:
    t = (sql_type or "").strip().upper()
    if t == "V":
        return "view"
    if t == "U":
        return "table"
    return "routine"


def search_objects(
    config: EnvConfig,
    *,
    needle: str,
    include_name: bool,
    include_definition: bool,
    include_routine: bool,
    include_view: bool,
    include_table: bool,
    max_rows: int = 500,
) -> list[ObjectSearchHit]:
    """
    한 환경(보통 기준 환경) DB에서 조건에 맞는 객체를 조회합니다.

    - 이름: schema.name, name, schema 각각에 대한 부분 일치(LIKE).
    - 본문: 프로시저·함수·뷰는 sys.sql_modules.definition, 테이블은 컬럼명·계산열 정의에 대한 LIKE.
    """
    if not include_name and not include_definition:
        raise ValueError("이름 또는 본문/컬럼 검색 중 하나 이상을 선택하세요.")
    if not include_routine and not include_view and not include_table:
        raise ValueError("프로시저·함수, 뷰, 테이블 중 하나 이상을 선택하세요.")

    pattern = build_contains_pattern(needle)
    if not pattern:
        return []

    hits: list[ObjectSearchHit] = []
    seen: set[tuple[str, str, str]] = set()
    limit = max(1, min(max_rows + 1, 2000))

    type_chars: list[str] = []
    if include_routine:
        type_chars.extend(list(ROUTINE_TYPES))
    if include_view:
        type_chars.append("V")

    if type_chars:
        in_ph = ", ".join("?" * len(type_chars))
        name_flag = 1 if include_name else 0
        def_flag = 1 if include_definition else 0
        sql_modules_sql = f"""
SELECT DISTINCT TOP ({limit})
    o.object_id,
    s.name AS schema_name,
    o.name,
    o.type AS object_type
FROM sys.objects o
INNER JOIN sys.sql_modules m ON m.object_id = o.object_id
INNER JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE o.type IN ({in_ph})
  AND (
        (? = 1 AND (s.name + N'.' + o.name LIKE ? OR o.name LIKE ? OR s.name LIKE ?))
        OR (? = 1 AND m.definition LIKE ?)
      )
ORDER BY s.name, o.name, o.object_id
"""
        params: tuple[object, ...] = (
            *type_chars,
            name_flag,
            pattern,
            pattern,
            pattern,
            def_flag,
            pattern,
        )
        with open_connection(config) as conn:
            cursor = conn.cursor()
            rows = fetch_all(cursor, sql_modules_sql, params)
        for row in rows:
            key = (row.schema_name, row.name, row.object_type)
            if key in seen:
                continue
            seen.add(key)
            hits.append(
                ObjectSearchHit(
                    schema_name=row.schema_name,
                    name=row.name,
                    object_id=int(row.object_id),
                    sql_type=str(row.object_type),
                    compare_kind=_sql_type_to_compare_kind(str(row.object_type)),
                )
            )

    if include_table:
        name_flag = 1 if include_name else 0
        def_flag = 1 if include_definition else 0
        table_sql = f"""
SELECT DISTINCT TOP ({limit})
    o.object_id,
    s.name AS schema_name,
    o.name,
    o.type AS object_type
FROM sys.objects o
INNER JOIN sys.schemas s ON s.schema_id = o.schema_id
LEFT JOIN sys.columns c ON c.object_id = o.object_id
LEFT JOIN sys.computed_columns cc
    ON cc.object_id = c.object_id AND cc.column_id = c.column_id
WHERE o.type = N'U'
  AND (
        (? = 1 AND (s.name + N'.' + o.name LIKE ? OR o.name LIKE ? OR s.name LIKE ?))
        OR (? = 1 AND (c.name LIKE ? OR ISNULL(cc.definition, N'') LIKE ?))
      )
ORDER BY s.name, o.name, o.object_id
"""
        params_t = (
            name_flag,
            pattern,
            pattern,
            pattern,
            def_flag,
            pattern,
            pattern,
        )
        with open_connection(config) as conn:
            cursor = conn.cursor()
            rows = fetch_all(cursor, table_sql, params_t)
        for row in rows:
            key = (row.schema_name, row.name, row.object_type)
            if key in seen:
                continue
            seen.add(key)
            hits.append(
                ObjectSearchHit(
                    schema_name=row.schema_name,
                    name=row.name,
                    object_id=int(row.object_id),
                    sql_type=str(row.object_type),
                    compare_kind="table",
                )
            )

    hits.sort(key=lambda h: (h.schema_name.lower(), h.name.lower(), h.compare_kind))
    return hits[: max_rows + 1]


def search_truncated(hits: list[ObjectSearchHit], max_rows: int) -> bool:
    return len(hits) > max_rows
