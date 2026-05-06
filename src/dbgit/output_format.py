"""프로시저/함수 비교 결과를 텍스트·JSON·마크다운으로 직렬화 (CLI·UI 공통)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict, Literal

if TYPE_CHECKING:
    from .compare import ProcDefinition

OutputFormat = Literal["text", "json", "markdown"]


def proc_comparison_payload(
    baseline: str,
    definitions: Dict[str, "ProcDefinition"],
) -> dict[str, object]:
    """JSON 직렬화 가능한 딕셔너리."""
    base_digest = definitions[baseline].digest
    env_entries: Dict[str, dict[str, object]] = {}
    for env_name, proc_def in definitions.items():
        env_entries[env_name] = {
            "object_id": proc_def.object_id,
            "schema_name": proc_def.schema_name,
            "name": proc_def.name,
            "full_name": proc_def.full_name,
            "digest": proc_def.digest,
            "same_as_baseline": proc_def.digest == base_digest,
        }
    diff_envs = [
        env_name
        for env_name, proc_def in definitions.items()
        if proc_def.digest != base_digest
    ]
    return {
        "baseline": baseline,
        "target_full_name": definitions[baseline].full_name,
        "environments": env_entries,
        "diff_environment_names": diff_envs,
        "all_same": len(diff_envs) == 0,
    }


def format_proc_comparison_text(baseline: str, definitions: Dict[str, "ProcDefinition"]) -> str:
    """기존 CLI 텍스트 형식."""
    base_def = definitions[baseline]
    lines: list[str] = []
    lines.append(f"기준 환경: {baseline} ({base_def.full_name})")
    lines.append("")
    lines.append("환경별 결과:")
    for env_name, proc_def in definitions.items():
        marker = "SAME" if proc_def.digest == base_def.digest else "DIFF"
        lines.append(f"- {env_name}: {marker} (object_id={proc_def.object_id})")
    lines.append("")
    diff_envs = [
        env_name for env_name, proc_def in definitions.items()
        if proc_def.digest != base_def.digest
    ]
    if diff_envs:
        lines.append("차이나는 환경:")
        lines.append(", ".join(diff_envs))
    else:
        lines.append("모든 환경이 동일합니다.")
    return "\n".join(lines)


def format_proc_comparison_json(baseline: str, definitions: Dict[str, "ProcDefinition"]) -> str:
    payload = proc_comparison_payload(baseline, definitions)
    definitions_dump: Dict[str, object] = {}
    for env_name, proc_def in definitions.items():
        definitions_dump[env_name] = {
            "object_id": proc_def.object_id,
            "schema_name": proc_def.schema_name,
            "name": proc_def.name,
            "full_name": proc_def.full_name,
            "digest": proc_def.digest,
            "definition": proc_def.definition,
        }
    payload["definitions_with_body"] = definitions_dump
    return json.dumps(payload, ensure_ascii=False, indent=2)


def format_proc_comparison_markdown(baseline: str, definitions: Dict[str, "ProcDefinition"]) -> str:
    base_def = definitions[baseline]
    lines: list[str] = [
        "## 프로시저·함수 비교 결과",
        "",
        f"- **기준 환경:** `{baseline}` — `{base_def.full_name}`",
        "",
        "| 환경 | 상태 | object_id | full_name |",
        "|:--|:--|--:|:--|",
    ]
    for env_name, proc_def in definitions.items():
        st = "SAME" if proc_def.digest == base_def.digest else "DIFF"
        lines.append(
            f"| {env_name} | {st} | {proc_def.object_id} | `{proc_def.full_name}` |"
        )
    diff_envs = [
        env_name for env_name, proc_def in definitions.items()
        if proc_def.digest != base_def.digest
    ]
    lines.append("")
    if diff_envs:
        lines.append(f"**차이 환경:** {', '.join(diff_envs)}")
    else:
        lines.append("**모든 환경이 동일합니다.**")
    return "\n".join(lines)


def format_proc_comparison(
    baseline: str,
    definitions: Dict[str, "ProcDefinition"],
    fmt: OutputFormat,
) -> str:
    if fmt == "json":
        return format_proc_comparison_json(baseline, definitions)
    if fmt == "markdown":
        return format_proc_comparison_markdown(baseline, definitions)
    return format_proc_comparison_text(baseline, definitions)
