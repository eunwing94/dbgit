"""테이블 스키마 직렬화(단위, DB 없음)."""

from types import SimpleNamespace

from dbgit.compare import table_schema_text_from_rows


def _row(**kwargs: object) -> SimpleNamespace:
    return SimpleNamespace(**kwargs)


def test_table_schema_text_from_rows_order_and_digest_stability() -> None:
    rows = [
        _row(
            column_id=1,
            column_name="Id",
            type_name="bigint",
            max_length=8,
            precision=19,
            scale=0,
            is_nullable=False,
            is_identity=True,
            is_computed=False,
            computed_definition="",
        ),
        _row(
            column_id=2,
            column_name="Nm",
            type_name="nvarchar",
            max_length=-1,
            precision=0,
            scale=0,
            is_nullable=True,
            is_identity=False,
            is_computed=True,
            computed_definition="  (  [Id]  + 1 ) ",
        ),
    ]
    text = table_schema_text_from_rows(rows)
    assert text.splitlines()[0] == "1|Id|bigint|8|19|0|0|1|0|"
    assert "2|Nm|nvarchar|-1|0|0|1|0|1|([Id]+1)" in text


def test_table_schema_text_empty() -> None:
    assert table_schema_text_from_rows([]) == ""
