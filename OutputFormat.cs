using System.Text.Json;

namespace Dbgit;

public static class OutputFormat
{
    private static List<string> DiffEnvNames(string baseline, Dictionary<string, ProcDefinition> definitions)
    {
        var baseDigest = definitions[baseline].Digest();
        return definitions
            .Where(kv => kv.Value.Digest() != baseDigest)
            .Select(kv => kv.Key)
            .ToList();
    }

    public static string FormatText(string baseline, Dictionary<string, ProcDefinition> definitions)
    {
        var baseDef = definitions[baseline];
        var sb = new StringBuilder();
        sb.AppendLine($"기준 환경: {baseline} ({baseDef.FullName})");
        sb.AppendLine();
        sb.AppendLine("환경별 결과:");

        foreach (var (envName, procDef) in definitions)
        {
            var marker = procDef.Digest() == baseDef.Digest() ? "SAME" : "DIFF";
            sb.AppendLine($"- {envName}: {marker} (object_id={procDef.ObjectId})");
        }

        sb.AppendLine();
        var diffEnvs = DiffEnvNames(baseline, definitions);
        if (diffEnvs.Count > 0)
        {
            sb.AppendLine("차이나는 환경:");
            sb.AppendLine(string.Join(", ", diffEnvs));
        }
        else
        {
            sb.AppendLine("모든 환경이 동일합니다.");
        }

        return sb.ToString().TrimEnd();
    }

    public static string FormatJson(string baseline, Dictionary<string, ProcDefinition> definitions)
    {
        var baseDigest = definitions[baseline].Digest();
        var envEntries = definitions.ToDictionary(
            kv => kv.Key,
            kv => (object)new
            {
                object_id = kv.Value.ObjectId,
                schema_name = kv.Value.SchemaName,
                name = kv.Value.Name,
                full_name = kv.Value.FullName,
                digest = kv.Value.Digest(),
                same_as_baseline = kv.Value.Digest() == baseDigest,
            });

        var diffNames = DiffEnvNames(baseline, definitions);
        var defsBody = definitions.ToDictionary(
            kv => kv.Key,
            kv => (object)new
            {
                object_id = kv.Value.ObjectId,
                schema_name = kv.Value.SchemaName,
                name = kv.Value.Name,
                full_name = kv.Value.FullName,
                digest = kv.Value.Digest(),
                definition = kv.Value.Definition,
            });

        var payload = new
        {
            baseline,
            target_full_name = definitions[baseline].FullName,
            environments = envEntries,
            diff_environment_names = diffNames,
            all_same = diffNames.Count == 0,
            definitions_with_body = defsBody,
        };

        return JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true });
    }

    public static string FormatMarkdown(string baseline, Dictionary<string, ProcDefinition> definitions)
    {
        var baseDef = definitions[baseline];
        var lines = new List<string>
        {
            "## 프로시저·함수 비교 결과",
            "",
            $"- **기준 환경:** `{baseline}` — `{baseDef.FullName}`",
            "",
            "| 환경 | 상태 | object_id | full_name |",
            "|:--|:--|--:|:--|",
        };

        foreach (var (envName, procDef) in definitions)
        {
            var st = procDef.Digest() == baseDef.Digest() ? "SAME" : "DIFF";
            lines.Add($"| {envName} | {st} | {procDef.ObjectId} | `{procDef.FullName}` |");
        }

        lines.Add("");
        var diffEnvs = DiffEnvNames(baseline, definitions);
        lines.Add(diffEnvs.Count > 0
            ? $"**차이 환경:** {string.Join(", ", diffEnvs)}"
            : "**모든 환경이 동일합니다.**");

        return string.Join(Environment.NewLine, lines);
    }

    public static string Format(string baseline, Dictionary<string, ProcDefinition> definitions, string fmt) =>
        fmt.ToLowerInvariant() switch
        {
            "json" => FormatJson(baseline, definitions),
            "markdown" => FormatMarkdown(baseline, definitions),
            _ => FormatText(baseline, definitions),
        };
}
