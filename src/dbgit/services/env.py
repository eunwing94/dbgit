"""환경별 DB 설정 로딩."""

from __future__ import annotations

from ..config import EnvConfig, load_env_config


def load_env_configs(env_names: list[str]) -> list[EnvConfig]:
    """환경 이름 목록을 `EnvConfig` 리스트로 변환합니다."""
    return [load_env_config(name) for name in env_names]
