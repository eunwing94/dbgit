from dbgit.object_search import build_contains_pattern, escape_sql_like_fragment


def test_escape_sql_like_fragment() -> None:
    assert escape_sql_like_fragment("100%") == "100[%]"
    assert escape_sql_like_fragment("a_b") == "a[_]b"
    assert escape_sql_like_fragment("x[y]") == "x[[]y]"


def test_build_contains_pattern() -> None:
    assert build_contains_pattern("SA") == "%SA%"
    assert build_contains_pattern("  A  ") == "%A%"
    assert build_contains_pattern(" %_[] ") == "%[%][_][[]]%"
