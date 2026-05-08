package com.dbgit;

import com.dbgit.cli.RootCommand;

import picocli.CommandLine;

public final class Main {
    public static void main(String[] args) {
        int code = new CommandLine(RootCommand.buildCompareCommand()).execute(args);
        System.exit(code);
    }
}
