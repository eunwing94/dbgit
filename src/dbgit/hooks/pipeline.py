"""등록된 훅을 순서대로 실행하는 파이프라인."""

from __future__ import annotations

from .types import Hook, HookContext, HookEventType


class HookPipeline:
    """여러 Hook을 하나의 실행 단위로 묶습니다."""

    def __init__(self, hooks: list[Hook]) -> None:
        self._hooks = list(hooks)

    def run(self, event_type: HookEventType, ctx: HookContext) -> None:
        for hook in self._hooks:
            hook.on_event(event_type, ctx)
