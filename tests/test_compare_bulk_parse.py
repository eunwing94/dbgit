"""일괄 비교용 object_id 느슨한 파싱."""

from dbgit import compare as compare_module


def test_parse_object_id_loose_int() -> None:
    assert compare_module._parse_object_id_loose("12345") == 12345


def test_parse_object_id_loose_excel_float_string() -> None:
    assert compare_module._parse_object_id_loose("12345.0") == 12345


def test_parse_object_id_loose_rejects_fractional() -> None:
    assert compare_module._parse_object_id_loose("12345.7") is None


def test_parse_object_id_loose_empty() -> None:
    assert compare_module._parse_object_id_loose("") is None
    assert compare_module._parse_object_id_loose("   ") is None


def test_parse_object_id_loose_name_not_int() -> None:
    assert compare_module._parse_object_id_loose("dbo.usp_X") is None
