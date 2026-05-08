use serde_json::json;

use crate::compare::ProcDefinition;

pub fn format_text(baseline: &str, defs: &std::collections::BTreeMap<String, ProcDefinition>) -> String {
    let b = &defs[baseline];
    let mut out = String::new();
    out.push_str(&format!("기준 환경: {} ({})\n\n", baseline, b.full_name()));
    out.push_str("환경별 결과:\n");
    for (env, p) in defs {
        let m = if p.digest_hex() == b.digest_hex() {
            "SAME"
        } else {
            "DIFF"
        };
        out.push_str(&format!("- {}: {} (object_id={})\n", env, m, p.object_id));
    }
    out.push('\n');
    let diff: Vec<_> = diff_envs(baseline, defs);
    if diff.is_empty() {
        out.push_str("모든 환경이 동일합니다.");
    } else {
        out.push_str("차이나는 환경:\n");
        out.push_str(&diff.join(", "));
    }
    out
}

fn diff_envs(
    baseline: &str,
    defs: &std::collections::BTreeMap<String, ProcDefinition>,
) -> Vec<String> {
    let bd = defs[baseline].digest_hex();
    defs.iter()
        .filter(|(_, v)| v.digest_hex() != bd)
        .map(|(k, _)| k.clone())
        .collect()
}

pub fn format_json(
    baseline: &str,
    defs: &std::collections::BTreeMap<String, ProcDefinition>,
) -> anyhow::Result<String> {
    let bd = defs[baseline].digest_hex();
    let mut envs = serde_json::Map::new();
    let mut bodies = serde_json::Map::new();
    for (k, v) in defs {
        envs.insert(
            k.clone(),
            json!({
                "object_id": v.object_id,
                "schema_name": v.schema_name,
                "name": v.name,
                "full_name": v.full_name(),
                "digest": v.digest_hex(),
                "same_as_baseline": v.digest_hex() == bd,
            }),
        );
        bodies.insert(
            k.clone(),
            json!({
                "object_id": v.object_id,
                "schema_name": v.schema_name,
                "name": v.name,
                "full_name": v.full_name(),
                "digest": v.digest_hex(),
                "definition": v.definition,
            }),
        );
    }
    let diff: Vec<String> = diff_envs(baseline, defs);
    let payload = json!({
        "baseline": baseline,
        "target_full_name": defs[baseline].full_name(),
        "environments": envs,
        "diff_environment_names": diff,
        "all_same": diff.is_empty(),
        "definitions_with_body": bodies,
    });
    Ok(serde_json::to_string_pretty(&payload)?)
}

pub fn format_md(baseline: &str, defs: &std::collections::BTreeMap<String, ProcDefinition>) -> String {
    let b = &defs[baseline];
    let mut s = String::new();
    s.push_str("## 프로시저·함수 비교 결과\n\n");
    s.push_str(&format!("- **기준 환경:** `{}` — `{}`\n\n", baseline, b.full_name()));
    s.push_str("| 환경 | 상태 | object_id | full_name |\n");
    s.push_str("|:--|:--|--:|:--|\n");
    for (env, p) in defs {
        let st = if p.digest_hex() == b.digest_hex() {
            "SAME"
        } else {
            "DIFF"
        };
        s.push_str(&format!(
            "| {} | {} | {} | `{}` |\n",
            env,
            st,
            p.object_id,
            p.full_name()
        ));
    }
    s.push('\n');
    let diff = diff_envs(baseline, defs);
    if diff.is_empty() {
        s.push_str("**모든 환경이 동일합니다.**");
    } else {
        s.push_str(&format!("**차이 환경:** {}", diff.join(", ")));
    }
    s
}
