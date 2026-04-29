from __future__ import annotations

from typing import Iterable

import pyodbc

from .config import EnvConfig


def build_connection_string(config: EnvConfig) -> str:
    # Encrypt=yes는 기본, 자체 서명 인증서 허용을 위해 TrustServerCertificate 사용
    return (
        f"DRIVER={{{config.driver}}};"
        f"SERVER={config.host},{config.port};"
        f"UID={config.user};"
        f"PWD={config.password};"
        f"DATABASE={config.database};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )


def open_connection(config: EnvConfig) -> pyodbc.Connection:
    conn_str = build_connection_string(config)
    return pyodbc.connect(conn_str, timeout=5)


def fetch_one(cursor: pyodbc.Cursor, query: str, params: Iterable[object]) -> pyodbc.Row | None:
    cursor.execute(query, params)
    return cursor.fetchone()
