namespace Dbgit.Render;

/// <summary>기본 렌더러들을 등록한 <see cref="RendererRegistry"/>를 생성합니다.</summary>
public static class RendererRegistryFactory
{
    public static RendererRegistry CreateDefault()
    {
        return new RendererRegistry()
            .Register(new TextRenderer())
            .Register(new JsonRenderer())
            .Register(new MarkdownRenderer());
    }

    public static OutputKind ParseOutputKind(string fmt) =>
        fmt.ToLowerInvariant() switch
        {
            "json" => OutputKind.Json,
            "markdown" => OutputKind.Markdown,
            _ => OutputKind.Text,
        };
}
