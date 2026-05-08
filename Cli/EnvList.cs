// CLI 입력 파싱/검증 유틸.
namespace Dbgit.Cli;

public static class EnvList
{
    public static List<string> Parse(string raw)
    {
        return raw
            .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Select(s => s.ToUpperInvariant())
            .Where(s => !string.IsNullOrWhiteSpace(s))
            .ToList();
    }

    public static void RequireContains(List<string> envs, string baseline)
    {
        if (!envs.Contains(baseline))
            throw new ArgumentException("baseline 환경이 envs 목록에 포함되어야 합니다.");
    }
}

