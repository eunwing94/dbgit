// dbgit CLI 엔트리포인트.
//
// - 옵션 파싱 → 검증 레이어 → 설정 로드 → 서비스(저장소/DB) → 훅 파이프라인 → 렌더러 레지스트리
using DotNetEnv;
using Dbgit.Cli;
using Dbgit.Config;
using Dbgit.Db;
using Dbgit.Errors;
using Dbgit.Hooks;
using Dbgit.Render;
using Dbgit.Service;
using Dbgit.Validation;

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

        var cli = new CliOptions(parsed.Proc, parsed.Envs, parsed.Baseline, parsed.Dotenv, parsed.Output);
        try
        {
            CliOptionsValidator.Validate(cli);
        }
        catch (DbgitException ex)
        {
            Console.Error.WriteLine(ExceptionMapper.ToUserMessage(ex));
            return 1;
        }

        if (File.Exists(parsed.Dotenv))
            Env.Load(parsed.Dotenv);

        var envList = EnvList.Parse(parsed.Envs);
        var baseline = parsed.Baseline.ToUpperInvariant();
        try
        {
            EnvList.RequireContains(envList, baseline);
        }
        catch (DbgitException ex)
        {
            Console.Error.WriteLine(ExceptionMapper.ToUserMessage(ex));
            return 1;
        }

        var outputKind = RendererRegistryFactory.ParseOutputKind(CliOptionsValidator.NormalizedOutput(cli));
        var renderers = RendererRegistryFactory.CreateDefault();

        var csBuilder = new SqlConnectionStringBuilder();
        var connectionFactory = new SqlConnectionFactory(csBuilder);
        var repository = new SqlProcDefinitionRepository(connectionFactory);
        var compareService = new ProcCompareService(repository);

        var hookPipeline = new HookPipeline(new IHook[] { new LoggingHook() });

        try
        {
            var configs = ConfigLoader.LoadEnvConfigs(envList);
            hookPipeline.Run(new HookEvent(HookEventType.BeforeCompare, DateTimeOffset.UtcNow, configs, parsed.Proc, null));

            var definitions = await compareService.CompareAcrossAsync(configs, parsed.Proc).ConfigureAwait(false);

            hookPipeline.Run(new HookEvent(HookEventType.AfterCompare, DateTimeOffset.UtcNow, configs, parsed.Proc, definitions));

            var rendered = renderers.Get(outputKind).Render(baseline, definitions);
            Console.WriteLine(rendered);
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"오류: {ExceptionMapper.ToUserMessage(ex)}");
            return 1;
        }
    }
}
