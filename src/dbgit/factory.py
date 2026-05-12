"""애플리케이션 기본 조립(훅 파이프라인 등)."""

from __future__ import annotations

from .hooks import HookPipeline, LoggingHook


def create_default_hook_pipeline() -> HookPipeline:
    """CLI·UI에서 공통으로 쓰는 기본 훅 파이프라인."""
    return HookPipeline([LoggingHook()])
