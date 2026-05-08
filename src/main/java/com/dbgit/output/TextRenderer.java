package com.dbgit.output;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.dbgit.domain.ProcDefinition;

public final class TextRenderer implements Renderer {
    @Override
    public OutputFormat format() {
        return OutputFormat.TEXT;
    }

    @Override
    public String render(String baseline, Map<String, ProcDefinition> defs) {
        ProcDefinition b = defs.get(baseline);
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("기준 환경: %s (%s)%n%n", baseline, b.fullName()));
        sb.append("환경별 결과:\n");
        for (var e : defs.entrySet()) {
            ProcDefinition p = e.getValue();
            String m = p.digestHex().equals(b.digestHex()) ? "SAME" : "DIFF";
            sb.append(String.format("- %s: %s (object_id=%d)%n", e.getKey(), m, p.objectId()));
        }
        sb.append("\n");
        List<String> diff = diffEnvs(baseline, defs);
        if (diff.isEmpty()) {
            sb.append("모든 환경이 동일합니다.");
        } else {
            sb.append("차이나는 환경:\n");
            sb.append(String.join(", ", diff));
        }
        return sb.toString();
    }

    private static List<String> diffEnvs(String baseline, Map<String, ProcDefinition> defs) {
        String bd = defs.get(baseline).digestHex();
        List<String> names = new ArrayList<>();
        for (var e : defs.entrySet()) {
            if (!e.getValue().digestHex().equals(bd)) names.add(e.getKey());
        }
        return names.stream().sorted().toList();
    }
}

