using Dbgit.Errors;

namespace Dbgit.Validation;

/// <summary>CLI에서 파싱된 원시 인자.</summary>
public sealed record CliOptions(
    string Proc,
    string EnvsRaw,
    string BaselineRaw,
    string DotenvPath,
    string OutputRaw
);

/// <summary>CLI 옵션 검증(스키마).</summary>
public static class CliOptionsValidator
{
    public static void Validate(CliOptions o)
    {
        if (string.IsNullOrWhiteSpace(o.Proc))
            throw new DbgitException(ErrorCode.InvalidArgument, "proc 인자가 필요합니다.");

        var fmt = o.OutputRaw.Trim().ToLowerInvariant();
        if (fmt is not ("text" or "json" or "markdown"))
            throw new DbgitException(ErrorCode.Output, "output은 text, json, markdown 중 하나여야 합니다.");
    }

    public static string NormalizedOutput(CliOptions o) =>
        o.OutputRaw.Trim().ToLowerInvariant();
}
