using DotNetEnv;

namespace Dbgit;

internal static class Program
{
    private static void PrintHelp()
    {
        Console.WriteLine("""
사용법: dbgit <proc> [옵션]

proc    프로시저/함수 object_id 또는 이름 (schema.name 권장)

옵션:
  --envs <목록>       콤마로 구분 (기본: PRD,STG,DEV,QA)
  --baseline <이름>   기준 환경 (기본: PRD)
  --dotenv <경로>     .env 파일 (기본: .env)
  -o, --output <형식> text | json | markdown (기본: text)
""");
    }

    private sealed record Args(string Proc, string Envs, string Baseline, string Dotenv, string Output);

    private static Args? ParseArgs(string[] args)
    {
        string? proc = null;
        var envs = string.Join(",", ConfigLoader.DefaultEnvs);
        var baseline = "PRD";
        var dotenv = ".env";
        var output = "text";

        for (var i = 0; i < args.Length; i++)
        {
            var a = args[i];
            if (a is "-h" or "--help")
            {
                PrintHelp();
                Environment.Exit(0);
            }
            if (a == "--envs" && i + 1 < args.Length)
            {
                envs = args[++i];
                continue;
            }
            if (a == "--baseline" && i + 1 < args.Length)
            {
                baseline = args[++i];
                continue;
            }
            if (a == "--dotenv" && i + 1 < args.Length)
            {
                dotenv = args[++i];
                continue;
            }
            if ((a == "-o" || a == "--output") && i + 1 < args.Length)
            {
                output = args[++i];
                continue;
            }
            if (!a.StartsWith('-'))
            {
                proc = a;
                continue;
            }
            Console.Error.WriteLine($"알 수 없는 옵션: {a}");
            return null;
        }

        if (string.IsNullOrWhiteSpace(proc))
        {
            Console.Error.WriteLine("proc 인자가 필요합니다.");
            PrintHelp();
            return null;
        }

        return new Args(proc.Trim(), envs, baseline.Trim(), dotenv, output.Trim());
    }

    public static async Task<int> Main(string[] args)
    {
        var parsed = ParseArgs(args);
        if (parsed is null)
            return 1;

        if (File.Exists(parsed.Dotenv))
            Env.Load(parsed.Dotenv);

        var envList = Cli.EnvList.Parse(parsed.Envs);
        var baseline = parsed.Baseline.ToUpperInvariant();
        try
        {
            Cli.EnvList.RequireContains(envList, baseline);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }

        var fmt = parsed.Output.ToLowerInvariant();
        if (fmt is not ("text" or "json" or "markdown"))
        {
            Console.Error.WriteLine("output은 text, json, markdown 중 하나여야 합니다.");
            return 1;
        }

        try
        {
            var configs = ConfigLoader.LoadEnvConfigs(envList);
            var hooks = new List<Hooks.IHook> { new Hooks.LoggingHook() };
            foreach (var h in hooks)
                h.OnEvent(new Hooks.HookEvent(Hooks.HookEventType.BeforeCompare, DateTimeOffset.UtcNow, configs, parsed.Proc, null));

            var definitions = await Compare.CompareAcrossEnvsAsync(configs, parsed.Proc).ConfigureAwait(false);
            foreach (var h in hooks)
                h.OnEvent(new Hooks.HookEvent(Hooks.HookEventType.AfterCompare, DateTimeOffset.UtcNow, configs, parsed.Proc, definitions));

            Console.WriteLine(OutputFormat.Format(baseline, definitions, fmt));
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"오류: {ex.Message}");
            return 1;
        }
    }
}
