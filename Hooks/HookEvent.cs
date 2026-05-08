// 비교 전/후 훅 이벤트 모델.
namespace Dbgit.Hooks;

public enum HookEventType
{
    BeforeCompare,
    AfterCompare
}

public sealed record HookEvent(
    HookEventType Type,
    DateTimeOffset At,
    IReadOnlyList<EnvConfig> Environments,
    string ProcIdentifier,
    IReadOnlyDictionary<string, ProcDefinition>? Results
);

