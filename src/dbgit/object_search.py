"""기준 DB에서 프로시저·함수·뷰·테이블을 이름/본문(정의) 조건으로 검색."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import NamedTuple

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


class ObjectSearchOutcome(NamedTuple):
    """`search_objects` 반환: 전체 조회 행 + SQL TOP 상한 도달 여부."""

    hits: list[ObjectSearchHit]
    reached_sql_fetch_cap: bool
    sql_fetch_cap: int


def object_search_sql_fetch_cap() -> int:
    """SQL `TOP (n)` 상한. 환경변수 `DBGIT_OBJECT_SEARCH_SQL_CAP` (기본 100000, 최대 500000)."""
    raw = os.getenv("DBGIT_OBJECT_SEARCH_SQL_CAP", "100000")
    try:
        return max(500, min(int(raw), 500_000))
    except ValueError:
        return 100_000


def escape_sql_like_fragment(fragment: str) -> str:
    """LIKE 패턴에 삽입할 문자열에서 %, _, [ 를 이스케이프합니다."""
    return fragment.replace("[", "[[]").replace("%", "[%]").replace("_", "[_]")


def build_contains_pattern(needle: str) -> str:
    """SQL LIKE '%...%' 용 패턴 (공백만 있는 입력은 허용하지 않음)."""
    stripped = needle.strip()
    if not stripped:
        return ""
    return f"%{escape_sql_like_fragment(stripped)}%"


def parse_or_terms(needle: str) -> list[str]:
    """
    검색어를 OR 토큰으로 분리합니다.

    - `|` (파이프): 각 구간을 별도 토큰
    - ` OR ` / ` or ` (단어 경계): 토큰 분리 (대소문자 무시)
    - 빈 토큰은 제거, 대소문자만 다른 중복은 하나로 합침
    """
    if not needle or not needle.strip():
        return []
    parts: list[str] = []
    for segment in re.split(r"\|", needle):
        for term in re.split(r"(?i)\s+or\s+", segment):
            t = term.strip()
            if t:
                parts.append(t)
    out: list[str] = []
    seen_lower: set[str] = set()
    for t in parts:
        k = t.lower()
        if k not in seen_lower:
            seen_lower.add(k)
            out.append(t)
    return out


def patterns_from_needle(needle: str) -> list[str]:
    """OR 분리 후 각 토큰에 대한 LIKE 패턴 목록."""
    return [p for t in parse_or_terms(needle) if (p := build_contains_pattern(t))]


def _module_name_match_sql(patterns: list[str]) -> tuple[str, list[object]]:
    """이름 관련 LIKE를 토큰별 OR 로 묶은 (sql, params)."""
    if not patterns:
        return "0=1", []
    chunks: list[str] = []
    params: list[object] = []
    for pat in patterns:
        chunks.append("(s.name + N'.' + o.name LIKE ? OR o.name LIKE ? OR s.name LIKE ?)")
        params.extend([pat, pat, pat])
    return "(" + " OR ".join(chunks) + ")", params


def _module_definition_match_sql(patterns: list[str]) -> tuple[str, list[object]]:
    if not patterns:
        return "0=1", []
    chunks = ["(m.definition LIKE ?)" for _ in patterns]
    return "(" + " OR ".join(chunks) + ")", list(patterns)


def _table_column_match_sql(patterns: list[str]) -> tuple[str, list[object]]:
    if not patterns:
        return "0=1", []
    chunks: list[str] = []
    params: list[object] = []
    for pat in patterns:
        chunks.append("(c.name LIKE ? OR ISNULL(cc.definition, N'') LIKE ?)")
        params.extend([pat, pat])
    return "(" + " OR ".join(chunks) + ")", params


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
) -> ObjectSearchOutcome:
    """
    한 환경(보통 기준 환경) DB에서 조건에 맞는 객체를 조회합니다.

    - 검색어: `|` 또는 ` OR ` / ` or ` 로 여러 토큰을 주면 **토큰 간 OR** (어느 하나라도 이름·본문에 맞으면 포함).
    - 이름: schema.name, name, schema 각각에 대한 부분 일치(LIKE).
    - 본문: 프로시저·함수·뷰는 sys.sql_modules.definition, 테이블은 컬럼명·계산열 정의에 대한 LIKE.
    - SQL 행 수 상한은 `DBGIT_OBJECT_SEARCH_SQL_CAP` (기본 100000). 상한에 걸리면 `reached_sql_fetch_cap` 이 True.
    """
    sql_cap = object_search_sql_fetch_cap()
    if not include_name and not include_definition:
        raise ValueError("이름 또는 본문/컬럼 검색 중 하나 이상을 선택하세요.")
    if not include_routine and not include_view and not include_table:
        raise ValueError("프로시저·함수, 뷰, 테이블 중 하나 이상을 선택하세요.")

    patterns = patterns_from_needle(needle)
    if not patterns:
        return ObjectSearchOutcome([], False, sql_cap)

    hits: list[ObjectSearchHit] = []
    seen: set[tuple[str, str, str]] = set()
    limit = sql_cap
    reached_sql_fetch_cap = False

    name_sql, name_params = _module_name_match_sql(patterns)
    def_sql, def_params = _module_definition_match_sql(patterns)
    col_sql, col_params = _table_column_match_sql(patterns)

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
        (? = 1 AND {name_sql})
        OR (? = 1 AND {def_sql})
      )
ORDER BY s.name, o.name, o.object_id
"""
        params: tuple[object, ...] = (
            *type_chars,
            name_flag,
            *name_params,
            def_flag,
            *def_params,
        )
        with open_connection(config) as conn:
            cursor = conn.cursor()
            rows = fetch_all(cursor, sql_modules_sql, params)
        if len(rows) >= limit:
            reached_sql_fetch_cap = True
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
        (? = 1 AND {name_sql})
        OR (? = 1 AND {col_sql})
      )
ORDER BY s.name, o.name, o.object_id
"""
        params_t: tuple[object, ...] = (
            name_flag,
            *name_params,
            def_flag,
            *col_params,
        )
        with open_connection(config) as conn:
            cursor = conn.cursor()
            rows = fetch_all(cursor, table_sql, params_t)
        if len(rows) >= limit:
            reached_sql_fetch_cap = True
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
    return ObjectSearchOutcome(
        hits=hits,
        reached_sql_fetch_cap=reached_sql_fetch_cap,
        sql_fetch_cap=limit,
    )
