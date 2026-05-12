using Dbgit.Errors;

namespace Dbgit.Config;

/// <summary><c>.env</c> / 환경 변수에서 <see cref="EnvConfig"/>를 로드합니다.</summary>
public static class ConfigLoader
{
    public static readonly string[] DefaultEnvs = ["PRD", "STG", "DEV", "QA"];

    private static string Require(string? value, string key, string envName)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new DbgitException(ErrorCode.Configuration, $"{envName} 설정 누락: {key}");
        return value;
    }

    public static EnvConfig LoadEnvConfig(string envName)
    {
        var prefix = envName.ToUpperInvariant();
        var host = Require(Environment.GetEnvironmentVariable($"{prefix}_HOST"), $"{prefix}_HOST", envName);
        var portRaw = Require(Environment.GetEnvironmentVariable($"{prefix}_PORT"), $"{prefix}_PORT", envName);
        var user = Require(Environment.GetEnvironmentVariable($"{prefix}_USER"), $"{prefix}_USER", envName);
        var password = Require(Environment.GetEnvironmentVariable($"{prefix}_PASSWORD"), $"{prefix}_PASSWORD", envName);
        var database = Require(Environment.GetEnvironmentVariable($"{prefix}_DATABASE"), $"{prefix}_DATABASE", envName);
        var driver = Environment.GetEnvironmentVariable($"{prefix}_DRIVER") ?? "ODBC Driver 18 for SQL Server";

        if (!int.TryParse(portRaw, out var port))
            throw new DbgitException(ErrorCode.Configuration, $"{envName} PORT 형식 오류: {portRaw}");

        return new EnvConfig(prefix, host, port, user, password, database, driver);
    }

    public static List<EnvConfig> LoadEnvConfigs(IEnumerable<string> names) =>
        names.Select(LoadEnvConfig).ToList();
}
