from datetime import datetime

import pandas as pd

from psdm_analysis.processing.series import (add_series,
                                             divide_positive_negative)

index = pd.date_range("2012-01-01 10:00:00", "2012-01-01 13:00:00", freq="h")
series = pd.Series(index=index, data=[1, 2, -2, 3])


def test_divide_series():
    positive, negative = divide_positive_negative(series)
    assert len(positive) == 4
    assert len(negative) == 4
    assert positive.sum() == 6
    assert negative.sum() == -2


def test_add_series():
    # test with different ranges
    start = datetime(year=2012, month=1, day=1, hour=11)
    end = datetime(year=2012, month=1, day=1, hour=13)
    series_short = series.copy(deep=True)[start:end]
    res = add_series(series, series_short, "test")
    assert res.sum() == 7

    # adding works with unsorted index
    series_unsorted = series[::-1]
    res_a = add_series(series, series_unsorted, "test")
    res_b = add_series(series, series, "test")
    assert res_a.equals(res_b)
