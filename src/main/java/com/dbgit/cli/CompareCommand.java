package com.dbgit.cli;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;

import com.dbgit.app.DbgitApp;
import com.dbgit.config.EnvConfig;
import com.dbgit.domain.ProcDefinition;
import com.dbgit.output.OutputFormat;
import com.dbgit.output.RendererRegistry;

import io.github.cdimascio.dotenv.Dotenv;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;

@Command(name = "compare", description = "프로시저/함수 정의를 환경별로 비교")
public final class CompareCommand implements Callable<Integer> {

    @Parameters(description = "프로시저/함수 object_id 또는 이름", arity = "1")
    String proc;

    @Option(names = "--envs", defaultValue = "PRD,STG,DEV,QA", description = "콤마로 구분")
    String envs;

    @Option(names = "--baseline", defaultValue = "PRD")
    String baseline;

    @Option(names = "--dotenv", defaultValue = ".env")
    String dotenvPath;

    @Option(names = "--output", defaultValue = "text", description = "text | json | markdown")
    String output;

    private final DbgitApp app;
    private final RendererRegistry renderers;

    public CompareCommand(DbgitApp app, RendererRegistry renderers) {
        this.app = app;
        this.renderers = renderers;
    }

    @Override
    public Integer call() {
        Dotenv dotenv = Dotenv.configure()
                .filename(dotenvPath)
                .ignoreIfMalformed()
                .ignoreIfMissing()
                .load();

        List<String> envList = EnvListParser.parse(envs);
        String bl = baseline.trim().toUpperCase();
        if (!envList.contains(bl)) {
            System.err.println("baseline 환경이 envs 목록에 포함되어야 합니다.");
            return 1;
        }

        OutputFormat fmt;
        try {
            fmt = OutputFormat.parse(output);
        } catch (IllegalArgumentException e) {
            System.err.println(e.getMessage());
            return 1;
        }

        List<EnvConfig> cfgs = new ArrayList<>();
        for (String n : envList) cfgs.add(EnvConfig.load(dotenv, n));

        Map<String, ProcDefinition> defs = app.compareAll(cfgs, proc.trim());
        String rendered = renderers.get(fmt).render(bl, defs);
        if (fmt == OutputFormat.TEXT) {
            System.out.print(rendered);
        } else {
            System.out.println(rendered);
        }
        return 0;
    }
}

