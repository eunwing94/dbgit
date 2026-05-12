namespace Dbgit.Hooks;

/// <summary>등록된 훅을 순서대로 실행하는 미들웨어.</summary>
public sealed class HookPipeline
{
    private readonly IReadOnlyList<IHook> _hooks;

    public HookPipeline(IEnumerable<IHook> hooks) =>
        _hooks = hooks.ToList();

    public void Run(HookEvent e)
    {
        foreach (var h in _hooks)
            h.OnEvent(e);
    }
}
