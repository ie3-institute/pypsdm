import pandas as pd
from numpy import float64

from pypsdm.processing.dataframe import add_df, divide_positive_negative

index = pd.date_range("2012-01-01 10:00:00", "2012-01-01 13:00:00", freq="h")
data = [1, 2, -2, 3]
df = pd.DataFrame(index=index, data={"p": data, "q": data.copy()})


def test_divide_positive_negative():
    positive, negative = divide_positive_negative(df)
    assert len(positive) == 4
    assert len(negative) == 4
    assert positive.p.sum() == 6
    assert positive.q.sum() == 6
    assert negative.p.sum() == -2
    assert negative.q.sum() == -2


def test_add_df():
    a = pd.DataFrame(index=[1, 3, 5], data={"a": [1, 2, 3], "b": [1, 2, 3]})
    b = pd.DataFrame(index=[2, 3], data={"a": [4, 5], "b": [4, 5]})
    res = add_df(a, b)

    expected = pd.DataFrame(
        index=[1, 2, 3, 5], data={"a": [1, 5, 7, 8], "b": [1, 5, 7, 8]}, dtype=float64
    )

    pd.testing.assert_frame_equal(res, expected)

    res_2 = add_df(b, a)
    pd.testing.assert_frame_equal(res, res_2)

    # adding works with unsorted index
    a = a.reindex(index=[5, 3, 1])
    b = b.reindex(index=[3, 2])
    res = add_df(a, b)
    pd.testing.assert_frame_equal(res, expected)
