namespace Dbgit.Config;

/// <summary>환경별 SQL Server 접속 설정.</summary>
public sealed record EnvConfig(
    string Name,
    string Host,
    int Port,
    string User,
    string Password,
    string Database,
    string Driver
);
