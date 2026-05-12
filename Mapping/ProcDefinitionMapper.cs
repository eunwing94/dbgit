using System.Text.RegularExpressions;
using Dbgit.Domain;

namespace Dbgit.Mapping;

/// <summary>행 DTO → <see cref="ProcDefinition"/> 변환 및 정규화.</summary>
public static class ProcDefinitionMapper
{
    private static string NormalizeDefinition(string definition) =>
        Regex.Replace(definition, @"\s+", "");

    public static ProcDefinition FromRow(ProcDefinitionRowDto row)
    {
        var def = row.DefinitionRaw ?? "";
        return new ProcDefinition(row.ObjectId, row.SchemaName, row.Name, def, NormalizeDefinition(def));
    }
}
