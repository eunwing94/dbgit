package com.dbgit.output;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import com.dbgit.domain.ProcDefinition;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

public final class JsonRenderer implements Renderer {

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    @Override
    public OutputFormat format() {
        return OutputFormat.JSON;
    }

    @Override
    public String render(String baseline, Map<String, ProcDefinition> defs) {
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
                            ProcDefinition p = e.getValue();
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
                            ProcDefinition p = e.getValue();
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

    private static List<String> diffEnvs(String baseline, Map<String, ProcDefinition> defs) {
        String bd = defs.get(baseline).digestHex();
        return defs.entrySet().stream()
                .filter(e -> !e.getValue().digestHex().equals(bd))
                .map(Map.Entry::getKey)
                .sorted()
                .toList();
    }
}

