import pandas as pd
from numpy import float64

from pypsdm.processing.series import add_series, divide_positive_negative


def test_divide_series():
    index = pd.date_range("2012-01-01 10:00:00", "2012-01-01 13:00:00", freq="h")
    series = pd.Series(index=index, data=[1, 2, -2, 3])
    positive, negative = divide_positive_negative(series)
    assert len(positive) == 4
    assert len(negative) == 4
    assert positive.sum() == 6
    assert negative.sum() == -2


def test_add_series():
    a = pd.Series(index=[1, 3, 5], data=[1, 2, 3], dtype=float64)
    b = pd.Series(index=[2, 3], data=[4, 5], dtype=float64)
    res = add_series(a, b, "test")

    expected = pd.Series(
        index=[1, 2, 3, 5], data=[1, 5, 7, 8], dtype=float64, name="test"
    )
    pd.testing.assert_series_equal(res, expected)

    res_2 = add_series(b, a, "test")
    pd.testing.assert_series_equal(res, res_2)

    # adding works with unsorted index
    a = a.reindex(index=[5, 3, 1])
    b = b.reindex(index=[3, 2])
    res = add_series(a, b, "test")
    pd.testing.assert_series_equal(res, expected)
