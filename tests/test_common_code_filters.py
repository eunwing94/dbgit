import pandas as pd

from dbgit.common_code_filters import build_common_code_summary, filter_common_code_df


def test_filter_hide_same():
    df = pd.DataFrame(
        {
            "COMP_CD": ["A", "A"],
            "CM_CD": ["X", "X"],
            "상태": ["SAME", "DIFF"],
            "비교환경": ["STG", "STG"],
        }
    )
    out = filter_common_code_df(df, hide_same=True)
    assert len(out) == 1
    assert out.iloc[0]["상태"] == "DIFF"


def test_filter_prefix():
    df = pd.DataFrame(
        {
            "COMP_CD": ["ERP", "OTH"],
            "CM_CD": ["CM01", "CM02"],
            "상태": ["DIFF", "DIFF"],
        }
    )
    out = filter_common_code_df(df, comp_cd_prefix="ERP")
    assert len(out) == 1


def test_summary_groups():
    df = pd.DataFrame(
        {
            "비교환경": ["STG", "STG", "QA"],
            "상태": ["DIFF", "DIFF", "SAME"],
        }
    )
    s = build_common_code_summary(df)
    assert "건수" in s.columns
    assert len(s) >= 2
