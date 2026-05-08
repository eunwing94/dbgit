// 렌더러 레지스트리(플러그인) 스켈레톤.
namespace Dbgit.Render;

public enum OutputKind
{
    Text,
    Json,
    Markdown
}

public interface IRenderer
{
    OutputKind Kind { get; }
    string Render(string baseline, Dictionary<string, ProcDefinition> definitions);
}

public sealed class RendererRegistry
{
    private readonly Dictionary<OutputKind, IRenderer> _map = new();

    public RendererRegistry Register(IRenderer r)
    {
        _map[r.Kind] = r;
        return this;
    }

    public IRenderer Get(OutputKind kind)
    {
        if (_map.TryGetValue(kind, out var r))
            return r;
        throw new InvalidOperationException($"등록되지 않은 렌더러: {kind}");
    }
}

