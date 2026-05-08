package com.dbgit;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;

import io.github.cdimascio.dotenv.Dotenv;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;

@Command(name = "dbgit", mixinStandardHelpOptions = true, version = "dbgit 0.1")
public final class Main implements Callable<Integer> {

    @Parameters(description = "프로시저/함수 object_id 또는 이름", arity = "1")
    String proc;

    @Option(names = "--envs", defaultValue = "PRD,STG,DEV,QA", description = "콤마로 구분")
    String envs;

    @Option(names = "--baseline", defaultValue = "PRD")
    String baseline;

    @Option(names = "--dotenv", defaultValue = ".env")
    String dotenv;

    @Option(names = "--output", defaultValue = "text", description = "text | json | markdown")
    String output;

    public static void main(String[] args) {
        int code = new CommandLine(new Main()).execute(args);
        System.exit(code);
    }

    @Override
    public Integer call() throws Exception {
        Dotenv env = Dotenv.configure()
                .filename(dotenv)
                .ignoreIfMalformed()
                .ignoreIfMissing()
                .load();

        List<String> envList = splitEnvs(envs);
        String bl = baseline.trim().toUpperCase();
        if (!envList.contains(bl)) {
            System.err.println("baseline 환경이 envs 목록에 포함되어야 합니다.");
            return 1;
        }

        String fmt = output.trim().toLowerCase();
        if (!fmt.equals("text") && !fmt.equals("json") && !fmt.equals("markdown")) {
            System.err.println("output은 text, json, markdown 중 하나여야 합니다.");
            return 1;
        }

        List<EnvConfig> cfgs = new ArrayList<>();
        for (String n : envList) {
            cfgs.add(EnvConfig.load(env, n));
        }

        Map<String, ProcCompare.ProcDefinition> defs = ProcCompare.compareAll(cfgs, proc.trim());

        switch (fmt) {
            case "json" -> System.out.println(Output.json(bl, defs));
            case "markdown" -> System.out.println(Output.markdown(bl, defs));
            default -> System.out.print(Output.text(bl, defs));
        }
        return 0;
    }

    private static List<String> splitEnvs(String raw) {
        return Arrays.stream(raw.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(s -> s.toUpperCase())
                .toList();
    }
}
