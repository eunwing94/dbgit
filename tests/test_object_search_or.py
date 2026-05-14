from dbgit.object_search import parse_or_terms, patterns_from_needle


def test_parse_or_terms_pipe() -> None:
    assert parse_or_terms("a|b") == ["a", "b"]
    assert parse_or_terms(" a | b ") == ["a", "b"]


def test_parse_or_terms_or_keyword() -> None:
    assert parse_or_terms("foo OR bar") == ["foo", "bar"]
    assert parse_or_terms("x or Y or z") == ["x", "Y", "z"]


def test_parse_or_terms_combined() -> None:
    assert parse_or_terms("a|b OR c") == ["a", "b", "c"]


def test_parse_or_terms_dedupe_case() -> None:
    assert parse_or_terms("A|a") == ["A"]


def test_patterns_from_needle_multiple() -> None:
    ps = patterns_from_needle("x OR y")
    assert len(ps) == 2
    assert ps[0] == "%x%"
    assert ps[1] == "%y%"
