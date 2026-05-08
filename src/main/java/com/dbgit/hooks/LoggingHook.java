package com.dbgit.hooks;

public final class LoggingHook implements Hook {

    @Override
    public void onEvent(HookEvent event) {
        if (event == null) return;
        switch (event.type()) {
            case BEFORE_COMPARE -> System.err.printf(
                    "[dbgit] beforeCompare envs=%d proc=%s%n",
                    event.environments().size(),
                    event.procIdentifier()
            );
            case AFTER_COMPARE -> System.err.printf(
                    "[dbgit] afterCompare envs=%d proc=%s results=%d%n",
                    event.environments().size(),
                    event.procIdentifier(),
                    event.result() == null ? 0 : event.result().size()
            );
        }
    }
}

