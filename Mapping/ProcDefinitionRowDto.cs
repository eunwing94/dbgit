namespace Dbgit.Mapping;

/// <summary>DB reader 행을 도메인 필드로 옮기기 위한 DTO(매핑 전 단계).</summary>
public sealed record ProcDefinitionRowDto(
    int ObjectId,
    string SchemaName,
    string Name,
    string? DefinitionRaw
);
