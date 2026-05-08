// 환경별 DB 접속 설정 로딩.
//
// `.env`/환경변수에서 `{ENV}_HOST` 등의 키를 읽어 `EnvConfig`로 변환합니다.
namespace Dbgit;

public sealed record EnvConfig(
    string Name,
    string Host,
    int Port,
    string User,
    string Password,
    string Database,
    string Driver
);

public static class ConfigLoader
{
    public static readonly string[] DefaultEnvs = ["PRD", "STG", "DEV", "QA"];

    private static string Require(string? value, string key, string envName)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new InvalidOperationException($"{envName} 설정 누락: {key}");
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
            throw new InvalidOperationException($"{envName} PORT 형식 오류: {portRaw}");

        return new EnvConfig(prefix, host, port, user, password, database, driver);
    }

    public static List<EnvConfig> LoadEnvConfigs(IEnumerable<string> names) =>
        names.Select(LoadEnvConfig).ToList();
}
