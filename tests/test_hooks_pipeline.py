from dataclasses import replace

from dbgit.compare import ProcDefinition
from dbgit.hooks import HookContext, HookEventType, HookPipeline, LoggingHook


def test_hook_pipeline_runs_before_and_after():
    seen: list[tuple[str, HookContext]] = []

    class Capture:
        def on_event(self, event_type: HookEventType, ctx: HookContext) -> None:
            seen.append((event_type.value, ctx))

    p = ProcDefinition(1, "dbo", "x", "a", "a")
    defs = {"PRD": p}
    base = HookContext("dbo.x", ("PRD", "STG"), "PRD")
    pipe = HookPipeline([Capture()])
    pipe.run(HookEventType.BEFORE_COMPARE, base)
    pipe.run(HookEventType.AFTER_COMPARE, replace(base, definitions=defs))

    assert seen[0][0] == HookEventType.BEFORE_COMPARE.value
    assert seen[0][1].definitions is None
    assert seen[1][0] == HookEventType.AFTER_COMPARE.value
    assert seen[1][1].definitions == defs


def test_logging_hook_does_not_raise():
    pipe = HookPipeline([LoggingHook()])
    ctx = HookContext("dbo.x", ("PRD",), "PRD")
    pipe.run(HookEventType.BEFORE_COMPARE, ctx)
