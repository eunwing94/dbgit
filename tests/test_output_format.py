from dbgit.compare import ProcDefinition
from dbgit.output_format import (
    format_proc_comparison_json,
    format_proc_comparison_markdown,
    format_proc_comparison_text,
    proc_comparison_payload,
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
