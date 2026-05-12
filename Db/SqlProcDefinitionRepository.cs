using Microsoft.Data.SqlClient;
using Dbgit.Config;
using Dbgit.Domain;
using Dbgit.Errors;
using Dbgit.Mapping;

namespace Dbgit.Db;

/// <summary><c>sys.sql_modules</c> 기반 SQL Server 구현.</summary>
public sealed class SqlProcDefinitionRepository : IProcDefinitionRepository
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

    private readonly ISqlConnectionFactory _connections;

    public SqlProcDefinitionRepository(ISqlConnectionFactory connections) =>
        _connections = connections;

    private static int? ParseObjectId(string procIdentifier) =>
        int.TryParse(procIdentifier, out var id) ? id : null;

    public async Task<ProcDefinition> FetchAsync(EnvConfig config, string procIdentifier, CancellationToken ct = default)
    {
        var oid = ParseObjectId(procIdentifier);

        await using var conn = await _connections.OpenAsync(config, ct).ConfigureAwait(false);
        await using var cmd = new SqlCommand(ProcQuery, conn);
        cmd.Parameters.AddWithValue("@oid", (object?)oid ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@pname", procIdentifier);
        cmd.Parameters.AddWithValue("@qual", procIdentifier);
        cmd.Parameters.AddWithValue("@oid2", (object?)oid ?? DBNull.Value);

        await using var reader = await cmd.ExecuteReaderAsync(ct).ConfigureAwait(false);
        if (!await reader.ReadAsync(ct).ConfigureAwait(false))
            throw new DbgitException(ErrorCode.NotFound, $"{config.Name}에서 프로시저를 찾지 못했습니다: {procIdentifier}");

        var dto = new ProcDefinitionRowDto(
            reader.GetInt32(0),
            reader.GetString(1),
            reader.GetString(2),
            reader.IsDBNull(3) ? null : reader.GetString(3));

        return ProcDefinitionMapper.FromRow(dto);
    }
}
