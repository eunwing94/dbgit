using Dbgit.Config;

namespace Dbgit.Db;

/// <summary>SQL 연결 문자열 생성.</summary>
public interface IConnectionStringBuilder
{
    string Build(EnvConfig config);
}

public sealed class SqlConnectionStringBuilder : IConnectionStringBuilder
{
    public string Build(EnvConfig c) =>
        $"Server=tcp:{c.Host},{c.Port};Database={c.Database};User Id={c.User};Password={c.Password};"
        + "Encrypt=True;TrustServerCertificate=True;Connection Timeout=5;";
}
