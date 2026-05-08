package com.dbgit;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

public final class Output {

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    public static String text(String baseline, Map<String, ProcCompare.ProcDefinition> defs) {
        ProcCompare.ProcDefinition b = defs.get(baseline);
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("기준 환경: %s (%s)%n%n", baseline, b.fullName()));
        sb.append("환경별 결과:\n");
        for (var e : defs.entrySet()) {
            ProcCompare.ProcDefinition p = e.getValue();
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

    public static String json(String baseline, Map<String, ProcCompare.ProcDefinition> defs) {
        String bd = defs.get(baseline).digestHex();
        record EnvJson(int object_id, String schema_name, String name, String full_name, String digest,
                       boolean same_as_baseline) {
        }
        record BodyJson(int object_id, String schema_name, String name, String full_name, String digest,
                        String definition) {
        }
        Map<String, EnvJson> envs = defs.entrySet().stream()
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        e -> {
                            ProcCompare.ProcDefinition p = e.getValue();
                            return new EnvJson(
                                    p.objectId(),
                                    p.schemaName(),
                                    p.name(),
                                    p.fullName(),
                                    p.digestHex(),
                                    p.digestHex().equals(bd));
                        }
                ));
        Map<String, BodyJson> bodies = defs.entrySet().stream()
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        e -> {
                            ProcCompare.ProcDefinition p = e.getValue();
                            return new BodyJson(
                                    p.objectId(),
                                    p.schemaName(),
                                    p.name(),
                                    p.fullName(),
                                    p.digestHex(),
                                    p.definition());
                        }
                ));
        List<String> diff = diffEnvs(baseline, defs);
        record Payload(
                String baseline,
                String target_full_name,
                Map<String, EnvJson> environments,
                List<String> diff_environment_names,
                boolean all_same,
                Map<String, BodyJson> definitions_with_body
        ) {
        }
        Payload p = new Payload(
                baseline,
                defs.get(baseline).fullName(),
                envs,
                diff,
                diff.isEmpty(),
                bodies);
        return GSON.toJson(p);
    }

    public static String markdown(String baseline, Map<String, ProcCompare.ProcDefinition> defs) {
        ProcCompare.ProcDefinition b = defs.get(baseline);
        StringBuilder sb = new StringBuilder();
        sb.append("## 프로시저·함수 비교 결과\n\n");
        sb.append(String.format("- **기준 환경:** `%s` — `%s`\n\n", baseline, b.fullName()));
        sb.append("| 환경 | 상태 | object_id | full_name |\n");
        sb.append("|:--|:--|--:|:--|\n");
        for (var e : defs.entrySet()) {
            ProcCompare.ProcDefinition p = e.getValue();
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

    private static List<String> diffEnvs(String baseline, Map<String, ProcCompare.ProcDefinition> defs) {
        String bd = defs.get(baseline).digestHex();
        List<String> names = new ArrayList<>();
        for (var e : defs.entrySet()) {
            if (!e.getValue().digestHex().equals(bd)) {
                names.add(e.getKey());
            }
        }
        return names.stream().sorted().collect(Collectors.toList());
    }
}
