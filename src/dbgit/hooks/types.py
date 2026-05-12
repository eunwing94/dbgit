"""비교 전후 훅 이벤트 타입."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from dbgit.compare import ProcDefinition


class HookEventType(str, Enum):
    """훅이 받는 이벤트 구분."""

    BEFORE_COMPARE = "before_compare"
    AFTER_COMPARE = "after_compare"


@dataclass(frozen=True)
class HookContext:
    """훅에 전달되는 컨텍스트."""

    proc_identifier: str
    env_names: tuple[str, ...]
    baseline: str
    definitions: dict[str, ProcDefinition] | None = None


class Hook(Protocol):
    """비교 파이프라인 훅."""

    def on_event(self, event_type: HookEventType, ctx: HookContext) -> None:
        """이벤트 발생 시 호출."""
