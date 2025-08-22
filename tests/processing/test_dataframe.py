import pandas as pd
from numpy import float64

from pypsdm.processing.dataframe import (
    add_df,
    divide_positive_negative,
    filter_data_for_time_interval,
)

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
    b = pd.DataFrame(index=[2, 3], data={"a": [4.0, 5.0], "b": [4.0, 5.0]})
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


def test_filter_data_for_time_interval():
    input_data = {
        "time": [
            "2016-04-01 17:30:00",
            "2016-04-01 18:15:00",
            "2016-04-01 19:30:00",
            "2016-04-01 20:45:00",
        ],
        "p": [0.022, 0.0, 0.022, 0.0],
        "q": [0.0, 0.0, 0.0, 0.0],
    }

    input_df = pd.DataFrame(input_data)

    input_df["time"] = pd.to_datetime(input_df["time"])
    input_df.set_index("time", inplace=True)

    start_1 = pd.to_datetime("2016-04-01 17:00:00")
    end_1 = pd.to_datetime("2016-04-01 21:00:00")
    res_1 = filter_data_for_time_interval(input_df, start_1, end_1)

    expected_data_1 = {
        "p": [0.022, 0.000, 0.022, 0.000],
        "q": [0.000, 0.000, 0.000, 0.000],
    }

    expected_index_1 = [
        pd.Timestamp("2016-04-01 17:30:00"),
        pd.Timestamp("2016-04-01 18:15:00"),
        pd.Timestamp("2016-04-01 19:30:00"),
        pd.Timestamp("2016-04-01 20:45:00"),
    ]

    expected_1 = pd.DataFrame(expected_data_1)
    expected_1.index = expected_index_1
    expected_1.index.name = "time"

    pd.testing.assert_frame_equal(res_1, expected_1)

    start_2 = pd.to_datetime("2016-04-01 17:30:00")
    end_2 = pd.to_datetime("2016-04-01 21:00:00")
    res_2 = filter_data_for_time_interval(input_df, start_2, end_2)

    expected_data_2 = {
        "p": [0.022, 0.000, 0.022, 0.000],
        "q": [0.000, 0.000, 0.000, 0.000],
    }

    expected_index_2 = [
        pd.Timestamp("2016-04-01 17:30:00"),
        pd.Timestamp("2016-04-01 18:15:00"),
        pd.Timestamp("2016-04-01 19:30:00"),
        pd.Timestamp("2016-04-01 20:45:00"),
    ]

    expected_2 = pd.DataFrame(expected_data_2)
    expected_2.index = expected_index_2
    expected_2.index.name = "time"

    pd.testing.assert_frame_equal(res_2, expected_2)

    start_2 = pd.to_datetime("2016-04-01 18:00:00")
    end_2 = pd.to_datetime("2016-04-01 21:00:00")
    res_2 = filter_data_for_time_interval(input_df, start_2, end_2)

    expected_data_2 = {
        "p": [0.022, 0.000, 0.022, 0.000],
        "q": [0.000, 0.000, 0.000, 0.000],
    }

    expected_index_2 = [
        pd.Timestamp("2016-04-01 18:00:00"),
        pd.Timestamp("2016-04-01 18:15:00"),
        pd.Timestamp("2016-04-01 19:30:00"),
        pd.Timestamp("2016-04-01 20:45:00"),
    ]

    expected_2 = pd.DataFrame(expected_data_2)
    expected_2.index = expected_index_2
    expected_2.index.name = "time"

    pd.testing.assert_frame_equal(res_2, expected_2)

    start_3 = pd.to_datetime("2016-04-01 18:15:00")
    end_3 = pd.to_datetime("2016-04-01 21:00:00")
    res_3 = filter_data_for_time_interval(input_df, start_3, end_3)

    expected_data_3 = {"p": [0.000, 0.022, 0.000], "q": [0.000, 0.000, 0.000]}

    expected_index_3 = [
        pd.Timestamp("2016-04-01 18:15:00"),
        pd.Timestamp("2016-04-01 19:30:00"),
        pd.Timestamp("2016-04-01 20:45:00"),
    ]

    expected_3 = pd.DataFrame(expected_data_3)
    expected_3.index = expected_index_3
    expected_3.index.name = "time"

    pd.testing.assert_frame_equal(res_3, expected_3)

    start_4 = pd.to_datetime("2016-04-01 17:00:00")
    end_4 = pd.to_datetime("2016-04-01 18:30:00")
    res_4 = filter_data_for_time_interval(input_df, start_4, end_4)

    expected_data_4 = {"p": [0.022, 0.000], "q": [0.000, 0.000]}

    expected_index_4 = [
        pd.Timestamp("2016-04-01 17:30:00"),
        pd.Timestamp("2016-04-01 18:15:00"),
    ]

    expected_4 = pd.DataFrame(expected_data_4)
    expected_4.index = expected_index_4
    expected_4.index.name = "time"

    pd.testing.assert_frame_equal(res_4, expected_4)

    start_5 = pd.to_datetime("2016-04-01 17:00:00")
    end_5 = pd.to_datetime("2016-04-01 17:15:00")
    res_5 = filter_data_for_time_interval(input_df, start_5, end_5)

    expected_data_5 = {
        "p": [],
        "q": [],
    }

    expected_index_5 = pd.DatetimeIndex([])

    expected_5 = pd.DataFrame(expected_data_5)
    expected_5.index = expected_index_5
    expected_5.index.name = "time"

    pd.testing.assert_frame_equal(res_5, expected_5)
