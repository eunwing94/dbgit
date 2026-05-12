using Dbgit.Config;
using Dbgit.Domain;

namespace Dbgit.Db;

/// <summary>프로시저/함수 정의 조회 저장소.</summary>
public interface IProcDefinitionRepository
{
    Task<ProcDefinition> FetchAsync(EnvConfig config, string procIdentifier, CancellationToken ct = default);
}
