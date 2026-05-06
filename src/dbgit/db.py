"""pyodbc 연결 문자열 생성 및 연결(재시도) 헬퍼."""

from __future__ import annotations

import logging
import os
import time
from typing import Iterable

import pyodbc

from .config import EnvConfig

logger = logging.getLogger("dbgit.db")

RETRIES_ENV = "DBGIT_DB_MAX_RETRIES"
DELAY_ENV = "DBGIT_DB_RETRY_DELAY_SEC"


def build_connection_string(config: EnvConfig) -> str:
    """SQL Server ODBC 연결 문자열. TLS·자체 서명 인증서 허용 옵션 포함."""
    return (
        f"DRIVER={{{config.driver}}};"
        f"SERVER={config.host},{config.port};"
        f"UID={config.user};"
        f"PWD={config.password};"
        f"DATABASE={config.database};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )


def _retry_params() -> tuple[int, float]:
    retries = int(os.getenv(RETRIES_ENV, "3"))
    delay = float(os.getenv(DELAY_ENV, "1.0"))
    return max(1, retries), max(0.0, delay)


def open_connection(config: EnvConfig) -> pyodbc.Connection:
    """
    연결 시도. DBGIT_DB_MAX_RETRIES(기본 3), DBGIT_DB_RETRY_DELAY_SEC(기본 1.0)만큼 재시도.
    """
    conn_str = build_connection_string(config)
    max_attempts, delay = _retry_params()
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                "DB 연결 시도 env=%s host=%s port=%s (시도 %s/%s)",
                config.name,
                config.host,
                config.port,
                attempt,
                max_attempts,
            )
            conn = pyodbc.connect(conn_str, timeout=5)
            logger.info("DB 연결 성공 env=%s", config.name)
            return conn
        except Exception as exc:
            last_err = exc
            logger.warning(
                "DB 연결 실패 env=%s 시도 %s/%s: %s",
                config.name,
                attempt,
                max_attempts,
                exc,
            )
            if attempt < max_attempts and delay > 0:
                time.sleep(delay)
    assert last_err is not None
    raise last_err


def fetch_one(cursor: pyodbc.Cursor, query: str, params: Iterable[object]) -> pyodbc.Row | None:
    """파라미터 바인딩 후 첫 행만 반환 (없으면 None)."""
    cursor.execute(query, params)
    return cursor.fetchone()
