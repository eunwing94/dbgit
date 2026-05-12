using Dbgit.Config;
using Dbgit.Domain;
using Dbgit.Db;

namespace Dbgit.Service;

/// <summary>환경 간 프로시저/함수 정의 비교 유스케이스.</summary>
public sealed class ProcCompareService
{
    private readonly IProcDefinitionRepository _repository;

    public ProcCompareService(IProcDefinitionRepository repository) =>
        _repository = repository;

    public async Task<Dictionary<string, ProcDefinition>> CompareAcrossAsync(
        IReadOnlyList<EnvConfig> configs,
        string procIdentifier,
        CancellationToken ct = default)
    {
        var results = new Dictionary<string, ProcDefinition>(StringComparer.Ordinal);
        foreach (var c in configs)
            results[c.Name] = await _repository.FetchAsync(c, procIdentifier, ct).ConfigureAwait(false);
        return results;
    }
}
