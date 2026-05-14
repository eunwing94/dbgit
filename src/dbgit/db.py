from __future__ import annotations

import os
from typing import Iterable

import pyodbc

from .config import EnvConfig


def _odbc_login_timeout_sec() -> int:
    """로그인(연결) 타임아웃 초. `DBGIT_ODBC_LOGIN_TIMEOUT_SEC`로 조절 (기본 60)."""
    raw = os.getenv("DBGIT_ODBC_LOGIN_TIMEOUT_SEC", "60")
    try:
        return max(5, min(int(raw), 600))
    except ValueError:
        return 60


def build_connection_string(config: EnvConfig) -> str:
    login_timeout = _odbc_login_timeout_sec()
    # Encrypt=yes는 기본, 자체 서명 인증서 허용을 위해 TrustServerCertificate 사용
    # Login Timeout: 드라이버가 TCP/로그인 완료까지 대기하는 시간 (HYT00 완화)
    return (
        f"DRIVER={{{config.driver}}};"
        f"SERVER={config.host},{config.port};"
        f"UID={config.user};"
        f"PWD={config.password};"
        f"DATABASE={config.database};"
        f"Login Timeout={login_timeout};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )


def open_connection(config: EnvConfig) -> pyodbc.Connection:
    conn_str = build_connection_string(config)
    return pyodbc.connect(conn_str, timeout=_odbc_login_timeout_sec())


def fetch_one(cursor: pyodbc.Cursor, query: str, params: Iterable[object]) -> pyodbc.Row | None:
    cursor.execute(query, params)
    return cursor.fetchone()


def fetch_all(cursor: pyodbc.Cursor, query: str, params: Iterable[object]) -> list[pyodbc.Row]:
    cursor.execute(query, params)
    return list(cursor.fetchall())
