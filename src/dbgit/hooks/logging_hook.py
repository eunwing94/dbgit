"""기본 로깅 훅."""

from __future__ import annotations

import logging

from .types import HookContext, HookEventType

logger = logging.getLogger("dbgit.hooks")


class LoggingHook:
    """비교 전후를 로그로 남깁니다."""

    def on_event(self, event_type: HookEventType, ctx: HookContext) -> None:
        logger.info(
            "hook event=%s proc=%s envs=%s baseline=%s defs=%s",
            event_type.value,
            ctx.proc_identifier,
            ",".join(ctx.env_names),
            ctx.baseline,
            None if ctx.definitions is None else len(ctx.definitions),
        )
