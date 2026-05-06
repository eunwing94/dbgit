using Microsoft.Data.SqlClient;

namespace Dbgit;

public static class Db
{
    private const string RetriesEnv = "DBGIT_DB_MAX_RETRIES";
    private const string DelayEnv = "DBGIT_DB_RETRY_DELAY_SEC";

    public static string BuildConnectionString(EnvConfig c) =>
        $"Server=tcp:{c.Host},{c.Port};Database={c.Database};User Id={c.User};Password={c.Password};"
        + "Encrypt=True;TrustServerCertificate=True;Connection Timeout=5;";

    private static (int Max, double DelaySec) RetryParams()
    {
        var max = Math.Max(1, int.TryParse(Environment.GetEnvironmentVariable(RetriesEnv), out var m) ? m : 3);
        var delay = double.TryParse(Environment.GetEnvironmentVariable(DelayEnv), out var d) ? d : 1.0;
        delay = Math.Max(0, delay);
        return (max, delay);
    }

    public static async Task<SqlConnection> ConnectWithRetryAsync(EnvConfig cfg, CancellationToken ct = default)
    {
        var (maxAttempts, delaySec) = RetryParams();
        Exception? last = null;

        for (var attempt = 1; attempt <= maxAttempts; attempt++)
        {
            try
            {
                var conn = new SqlConnection(BuildConnectionString(cfg));
                await conn.OpenAsync(ct).ConfigureAwait(false);
                return conn;
            }
            catch (Exception ex)
            {
                last = ex;
                Console.Error.WriteLine($"DB 연결 실패 env={cfg.Name} 시도 {attempt}/{maxAttempts}: {ex.Message}");
                if (attempt < maxAttempts && delaySec > 0)
                    await Task.Delay(TimeSpan.FromSeconds(delaySec), ct).ConfigureAwait(false);
            }
        }

        throw last ?? new InvalidOperationException("연결 실패");
    }
}
