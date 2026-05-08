package com.dbgit;

/**
 * Java CLI 엔트리포인트.
 *
 * 현재 구현은 `picocli` 기반 커맨드(`com.dbgit.cli.CompareCommand`)를 실행합니다.
 */
import com.dbgit.cli.RootCommand;

import picocli.CommandLine;

public final class Main {
    public static void main(String[] args) {
        int code = new CommandLine(RootCommand.buildCompareCommand()).execute(args);
        System.exit(code);
    }
}
