package com.dbgit.output;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.dbgit.domain.ProcDefinition;

public final class MarkdownRenderer implements Renderer {
    @Override
    public OutputFormat format() {
        return OutputFormat.MARKDOWN;
    }

    @Override
    public String render(String baseline, Map<String, ProcDefinition> defs) {
        ProcDefinition b = defs.get(baseline);
        StringBuilder sb = new StringBuilder();
        sb.append("## 프로시저·함수 비교 결과\n\n");
        sb.append(String.format("- **기준 환경:** `%s` — `%s`%n%n", baseline, b.fullName()));
        sb.append("| 환경 | 상태 | object_id | full_name |\n");
        sb.append("|:--|:--|--:|:--|\n");
        for (var e : defs.entrySet()) {
            ProcDefinition p = e.getValue();
            String st = p.digestHex().equals(b.digestHex()) ? "SAME" : "DIFF";
            sb.append(String.format("| %s | %s | %d | `%s` |%n", e.getKey(), st, p.objectId(), p.fullName()));
        }
        sb.append("\n");
        List<String> diff = diffEnvs(baseline, defs);
        if (diff.isEmpty()) {
            sb.append("**모든 환경이 동일합니다.**");
        } else {
            sb.append("**차이 환경:** ").append(String.join(", ", diff));
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

