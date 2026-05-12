package com.dbgit.cli;

import com.dbgit.factory.CompositionRoot;

import picocli.CommandLine.Command;

@Command(
        name = "dbgit",
        mixinStandardHelpOptions = true,
        version = "dbgit 0.2",
        description = "SQL Server 프로시저/함수 형상 비교 CLI"
)
public final class RootCommand {

    static CompareCommand buildCompareCommand() {
        return CompositionRoot.buildCompareCommand();
    }
}

