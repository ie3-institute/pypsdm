from pandas import DataFrame


def is_close(a, b, rel_tol=1e-09):
    return abs(a - b) <= rel_tol


def compare_dfs(a: DataFrame, b: DataFrame):
    assert (a.index.sort_values() == a.index.sort_values()).all()
    assert (a.columns.sort_values() == b.columns.sort_values()).all()
    assert a.sort_index().sort_index(axis=1).equals(b.sort_index().sort_index(axis=1))
