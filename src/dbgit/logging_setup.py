"""환경변수 기반 로깅 설정. 앱/CLI 진입 시 한 번 호출."""

from __future__ import annotations

import logging
import os

_LOGGERS = ("dbgit", "urllib3")


def configure_logging() -> None:
    """
    - DBGIT_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL, OFF (비활성)
    - DBGIT_LOG=1 일 때 기본 INFO (LEVEL 미지정 시)
    - 둘 다 없으면 WARNING
    """
    level_name = (os.getenv("DBGIT_LOG_LEVEL") or "").strip().upper()
    if level_name in ("OFF", "NONE", "DISABLE"):
        logging.disable(logging.CRITICAL)
        return

    if not level_name:
        if os.getenv("DBGIT_LOG", "").strip().lower() in ("1", "true", "yes", "on"):
            level_name = "INFO"
        else:
            level_name = "WARNING"

    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        root.setLevel(level)

    for name in _LOGGERS:
        logging.getLogger(name).setLevel(level)
