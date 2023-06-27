import pandas as pd
from pandas import DataFrame


def is_close(a, b, rel_tol=1e-09):
    return abs(a - b) <= rel_tol


def compare_dfs(a: DataFrame, b: DataFrame, check_like=True, **kwargs):
    if not len(a.columns) == len(b.columns):
        difference = set(a.columns).symmetric_difference(set(b.columns))
        raise AssertionError(f"Columns {difference} are not in both DataFrames")
    assert (
        a.index.sort_values() == a.index.sort_values()
    ).all(), "Different indexes in DataFrames"
    assert (
        a.columns.sort_values() == b.columns.sort_values()
    ).all(), "Different columns in DataFrames"
    pd.testing.assert_frame_equal(
        a,
        b,
        check_like=check_like,
        check_column_type=False,
        check_index_type=False,
        **kwargs,
    )
