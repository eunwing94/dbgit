using Dbgit.Config;
using Dbgit.Domain;

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

