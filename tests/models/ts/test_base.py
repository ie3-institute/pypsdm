from datetime import datetime

import pandas as pd
import pytest

from pypsdm.errors import ComparisonError
from pypsdm.models.ts.base import TIME_COLUMN_NAME, TimeSeries, TimeSeriesDict


def get_sample_data():
    data = pd.DataFrame(
        {
            TIME_COLUMN_NAME: [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
            ],
            "p": [0, 1, 2, 3],
        }
    )
    return data


def test_preprocess_data():
    data = pd.DataFrame({TIME_COLUMN_NAME: ["2021-01-01", "2021-01-02"], "p": [0, 1]})
    end = datetime(2021, 1, 3)
    result = TimeSeries.preprocess_data(data, end)
    assert result.index[-1] == pd.Timestamp("2021-01-03")
    assert result["p"][-1] == 1
    assert result.columns == ["p"]

    data = pd.DataFrame({TIME_COLUMN_NAME: ["2021-01-01", "2021-01-02"], "p": [0, 1]})
    result = TimeSeries.preprocess_data(data)
    assert len(data) == len(result)
    assert result.index[-1] == pd.Timestamp("2021-01-02")
    assert result["p"][-1] == 1


def test_interval():
    data = get_sample_data()
    ts = TimeSeries(data)
    result = ts.interval(datetime(2021, 1, 2), datetime(2021, 1, 3))
    assert len(result) == 2
    assert result.data.index[0] == pd.Timestamp("2021-01-02")
    assert result.data.index[-1] == pd.Timestamp("2021-01-03")
    assert result.data["p"][0] == 1
    assert result.data["p"][-1] == 2

    ts = TimeSeries(data)
    start = datetime(2021, 1, 2)
    end = datetime(2021, 1, 2, 1)
    result = ts.interval(start, end)
    assert len(result) == 2
    assert result.data.index[0] == pd.Timestamp("2021-01-02")
    assert result.data.index[-1] == pd.Timestamp("2021-01-02 01:00:00")
    assert result.data["p"][0] == 1
    assert result.data["p"][-1] == 1
    assert result == ts[start:end]


def test_eq():
    data = get_sample_data()
    ts = TimeSeries(data)
    assert ts == TimeSeries(data)
    assert ts != TimeSeries(data[1:])


def get_sample_dict():
    a = get_sample_data()
    b = get_sample_data()
    c = get_sample_data()
    return TimeSeriesDict({"a": TimeSeries(a), "b": TimeSeries(b), "c": TimeSeries(c)})


def test_dct_subset():
    dct = get_sample_dict()
    assert dct.subset(["a", "b"]).keys() == {"a", "b"}
    st, rmd = dct.subset_split(["a", "b"])
    assert st.keys() == {"a", "b"}
    assert rmd.keys() == {"c"}


def test_dct_interval():
    dct = get_sample_dict()
    result = dct.interval(datetime(2021, 1, 2), datetime(2021, 1, 3))
    assert len(result) == 3
    for key in ["a", "b", "c"]:
        assert result[key].data.index[0] == pd.Timestamp("2021-01-02")
        assert result[key].data.index[-1] == pd.Timestamp("2021-01-03")
        assert len(result[key]) == 2


def test_compare():
    dct = get_sample_dict()
    dct2 = get_sample_dict()
    assert dct.compare(dct2) is None
    dct2["d"] = TimeSeries(get_sample_data())
    # raises comparison error
    with pytest.raises(ComparisonError):
        dct.compare(dct2)
