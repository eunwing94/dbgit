using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.Data.SqlClient;

// 비교 유스케이스.
//
// 각 환경에서 프로시저/함수 정의를 조회하고 정규화+해시로 SAME/DIFF를 판정합니다.
namespace Dbgit;

public sealed record ProcDefinition(
    int ObjectId,
    string SchemaName,
    string Name,
    string Definition,
    string NormalizedDefinition
)
{
    public string FullName => $"{SchemaName}.{Name}";

    public string Digest()
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(NormalizedDefinition));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }
}

public static class Compare
{
    private const string ProcQuery = """
SELECT TOP 1
    o.object_id,
    s.name AS schema_name,
    o.name,
    m.definition
FROM sys.objects o
JOIN sys.sql_modules m ON o.object_id = m.object_id
JOIN sys.schemas s ON o.schema_id = s.schema_id
WHERE o.type IN ('P', 'PC', 'FN', 'IF', 'TF')
  AND (
        o.object_id = @oid
        OR o.name = @pname
        OR s.name + '.' + o.name = @qual
  )
ORDER BY
    CASE WHEN o.object_id = @oid2 THEN 0 ELSE 1 END,
    o.name;
""";

    private static int? ParseObjectId(string procIdentifier) =>
        int.TryParse(procIdentifier, out var id) ? id : null;

    private static string NormalizeDefinition(string definition) =>
        Regex.Replace(definition, @"\s+", "");

    public static async Task<ProcDefinition> FetchProcDefinitionAsync(
        EnvConfig config,
        string procIdentifier,
        CancellationToken ct = default)
    {
        var oid = ParseObjectId(procIdentifier);

        await using var conn = await Db.ConnectWithRetryAsync(config, ct).ConfigureAwait(false);
        await using var cmd = new SqlCommand(ProcQuery, conn);
        cmd.Parameters.AddWithValue("@oid", (object?)oid ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@pname", procIdentifier);
        cmd.Parameters.AddWithValue("@qual", procIdentifier);
        cmd.Parameters.AddWithValue("@oid2", (object?)oid ?? DBNull.Value);

        await using var reader = await cmd.ExecuteReaderAsync(ct).ConfigureAwait(false);
        if (!await reader.ReadAsync(ct).ConfigureAwait(false))
            throw new InvalidOperationException($"{config.Name}에서 프로시저를 찾지 못했습니다: {procIdentifier}");

        var objectId = reader.GetInt32(0);
        var schemaName = reader.GetString(1);
        var name = reader.GetString(2);
        var definition = reader.IsDBNull(3) ? "" : reader.GetString(3);
        var normalized = NormalizeDefinition(definition);
        return new ProcDefinition(objectId, schemaName, name, definition, normalized);
    }

    public static async Task<Dictionary<string, ProcDefinition>> CompareAcrossEnvsAsync(
        IEnumerable<EnvConfig> configs,
        string procIdentifier,
        CancellationToken ct = default)
    {
        var results = new Dictionary<string, ProcDefinition>();
        foreach (var c in configs)
            results[c.Name] = await FetchProcDefinitionAsync(c, procIdentifier, ct).ConfigureAwait(false);
        return results;
    }
}
