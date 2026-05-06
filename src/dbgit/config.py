"""환경별 DB 접속 정보를 OS 환경변수에서 읽어 `EnvConfig`로 만든다."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EnvConfig:
    """한 환경(PRD, STG 등)의 SQL Server 접속 설정."""

    name: str
    host: str
    port: int
    user: str
    password: str
    database: str
    driver: str


def _require(value: str | None, key: str, env_name: str) -> str:
    """필수 환경변수가 비어 있으면 예외."""
    if not value:
        raise ValueError(f"{env_name} 설정 누락: {key}")
    return value


def load_env_config(env_name: str) -> EnvConfig:
    """
    `{PREFIX}_HOST`, `{PREFIX}_PORT`, … 형태의 변수를 읽는다.
    PREFIX는 env_name을 대문자로 한 값 (예: PRD_HOST).
    선택: `{PREFIX}_DRIVER` (기본 ODBC Driver 18 for SQL Server).
    """
    prefix = env_name.upper()
    host = _require(os.getenv(f"{prefix}_HOST"), f"{prefix}_HOST", env_name)
    port_raw = _require(os.getenv(f"{prefix}_PORT"), f"{prefix}_PORT", env_name)
    user = _require(os.getenv(f"{prefix}_USER"), f"{prefix}_USER", env_name)
    password = _require(os.getenv(f"{prefix}_PASSWORD"), f"{prefix}_PASSWORD", env_name)
    database = _require(os.getenv(f"{prefix}_DATABASE"), f"{prefix}_DATABASE", env_name)
    driver = os.getenv(f"{prefix}_DRIVER", "ODBC Driver 18 for SQL Server")

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError(f"{env_name} PORT 형식 오류: {port_raw}") from exc

    return EnvConfig(
        name=env_name.upper(),
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        driver=driver,
    )
