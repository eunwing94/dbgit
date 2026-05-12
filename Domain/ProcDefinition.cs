using System.Security.Cryptography;
using System.Text;

namespace Dbgit.Domain;

/// <summary>단일 환경에서 조회한 프로시저/함수 정의.</summary>
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
