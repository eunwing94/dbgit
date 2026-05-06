from dbgit.compare import ProcDefinition
from dbgit.output_format import (
    diff_environment_names,
    format_proc_comparison_json,
    format_proc_comparison_markdown,
    format_proc_comparison_text,
    proc_comparison_payload,
    proc_comparison_summary_rows,
)


def _defs():
    p = ProcDefinition(
        object_id=1,
        schema_name="dbo",
        name="p1",
        definition="CREATE PROC dbo.p1 AS SELECT 1",
        normalized_definition="CREATEPROCdbo.p1ASSELECT1",
    )
    return {"PRD": p, "STG": p}


def test_format_text_contains_baseline():
    text = format_proc_comparison_text("PRD", _defs())
    assert "PRD" in text
    assert "SAME" in text


def test_json_roundtrip_keys():
    js = format_proc_comparison_json("PRD", _defs())
    assert "baseline" in js
    assert "definitions_with_body" in js


def test_markdown_table():
    md = format_proc_comparison_markdown("PRD", _defs())
    assert "|" in md


def test_payload_summary():
    pl = proc_comparison_payload("PRD", _defs())
    assert pl["all_same"] is True


def test_diff_environment_names_and_summary_rows():
    defs = _defs()
    assert diff_environment_names("PRD", defs) == []
    rows = proc_comparison_summary_rows("PRD", defs)
    assert len(rows) == 2
    assert rows[0]["상태"] == "SAME"


def test_diff_environment_names_when_digest_differs():
    p_a = ProcDefinition(1, "dbo", "p", "CREATE PROC ...", "norm_a")
    p_b = ProcDefinition(1, "dbo", "p", "CREATE PROC ...", "norm_b")
    defs = {"PRD": p_a, "STG": p_b}
    assert diff_environment_names("PRD", defs) == ["STG"]
    rows = proc_comparison_summary_rows("PRD", defs)
    assert rows[1]["상태"] == "DIFF"
