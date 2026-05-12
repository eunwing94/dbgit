package com.dbgit.factory;

import com.dbgit.app.DbgitApp;
import com.dbgit.cli.CompareCommand;
import com.dbgit.db.ProcSqlRepository;
import com.dbgit.db.RetryPolicy;
import com.dbgit.db.RetryingDbConnector;
import com.dbgit.db.SqlServerConnector;
import com.dbgit.hooks.HookPipeline;
import com.dbgit.hooks.LoggingHook;
import com.dbgit.output.JsonRenderer;
import com.dbgit.output.MarkdownRenderer;
import com.dbgit.output.RendererRegistry;
import com.dbgit.output.TextRenderer;
import com.dbgit.service.ProcCompareService;

import java.util.List;

/**
 * 기본 의존성 조립(팩토리).
 */
public final class CompositionRoot {

    private CompositionRoot() {}

    public static CompareCommand buildCompareCommand() {
        var connector = new RetryingDbConnector(new SqlServerConnector(), RetryPolicy.fromEnv());
        var service = new ProcCompareService(connector, new ProcSqlRepository());
        var pipeline = new HookPipeline(List.of(new LoggingHook()));
        var app = new DbgitApp(service, pipeline);

        var registry = new RendererRegistry()
                .register(new TextRenderer())
                .register(new JsonRenderer())
                .register(new MarkdownRenderer());

        return new CompareCommand(app, registry);
    }
}
