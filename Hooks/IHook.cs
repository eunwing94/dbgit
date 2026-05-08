// 훅 인터페이스 및 기본 구현.
namespace Dbgit.Hooks;

public interface IHook
{
    void OnEvent(HookEvent e);
}

public sealed class LoggingHook : IHook
{
    public void OnEvent(HookEvent e)
    {
        if (e.Type == HookEventType.BeforeCompare)
        {
            Console.Error.WriteLine($"[dbgit] before_compare envs={e.Environments.Count} proc={e.ProcIdentifier}");
            return;
        }

        var resultsCount = e.Results?.Count ?? 0;
        Console.Error.WriteLine($"[dbgit] after_compare envs={e.Environments.Count} proc={e.ProcIdentifier} results={resultsCount}");
    }
}

