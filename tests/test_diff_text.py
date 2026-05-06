from dbgit.diff_text import build_comparable_lines, build_diff_text


def test_comparable_lines_skips_blank_only():
    lines = build_comparable_lines("  \n\nhello\n")
    assert len(lines) == 1
    assert lines[0][1] == "hello"


def test_build_diff_text_detects_change():
    a = "SELECT 1\nSELECT 2"
    b = "SELECT 1\nSELECT 3"
    la = build_comparable_lines(a)
    lb = build_comparable_lines(b)
    left, right = build_diff_text(la, lb)
    assert "SELECT 2" in left or "SELECT 3" in right
