package com.dbgit.cli;

import com.dbgit.app.DbgitApp;
import com.dbgit.db.ProcSqlRepository;
import com.dbgit.db.RetryPolicy;
import com.dbgit.db.RetryingDbConnector;
import com.dbgit.db.SqlServerConnector;
import com.dbgit.hooks.LoggingHook;
import com.dbgit.output.JsonRenderer;
import com.dbgit.output.MarkdownRenderer;
import com.dbgit.output.RendererRegistry;
import com.dbgit.output.TextRenderer;
import com.dbgit.service.ProcCompareService;

import picocli.CommandLine.Command;

@Command(
        name = "dbgit",
        mixinStandardHelpOptions = true,
        version = "dbgit 0.2",
        description = "SQL Server 프로시저/함수 형상 비교 CLI"
)
public final class RootCommand {

    static CompareCommand buildCompareCommand() {
        var connector = new RetryingDbConnector(new SqlServerConnector(), RetryPolicy.fromEnv());
        var service = new ProcCompareService(connector, new ProcSqlRepository());
        var app = new DbgitApp(service, java.util.List.of(new LoggingHook()));

        var registry = new RendererRegistry()
                .register(new TextRenderer())
                .register(new JsonRenderer())
                .register(new MarkdownRenderer());

        return new CompareCommand(app, registry);
    }
}

