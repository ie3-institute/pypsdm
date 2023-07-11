from datetime import datetime

import pandas as pd
import pytest

from psdm_analysis.models.enums import SystemParticipantsEnum
from psdm_analysis.models.result.power import PQResult


def create_sample_data(
    start_date: datetime, periods: int, freq: str = "h"
) -> pd.DataFrame:
    date_range = pd.date_range(start=start_date, periods=periods, freq=freq)
    data = {
        "p": pd.Series(range(periods), index=date_range),
        "q": pd.Series(range(periods, periods * 2), index=date_range),
    }
    data = pd.DataFrame(data)
    data.index.name = "time"
    return data


def create_custom_pq_res():
    data = create_sample_data(datetime(2023, 1, 1), 5)
    return PQResult(SystemParticipantsEnum.LOAD, "test-res", "test-res", data)


def test_get_slice():
    ts = create_custom_pq_res()
    start = datetime(2023, 1, 1, 1)
    stop = datetime(2023, 1, 1, 3)
    sliced_ts = ts[start:stop]

    assert isinstance(sliced_ts, PQResult)
    assert len(sliced_ts.data) == 3


def test_get_slice_invalid_types():
    ts = create_custom_pq_res()
    with pytest.raises(ValueError):
        _ = ts[0:2]


def test_get_datetime():
    ts = create_custom_pq_res()
    dt = datetime(2023, 1, 1)
    result_ts = ts[dt]

    assert isinstance(result_ts, PQResult)
    assert len(result_ts.data) == 1
    assert result_ts.data.index[0] == dt


def test_get_list_of_datetimes():
    ts = create_custom_pq_res()
    dt_list = [datetime(2023, 1, 1, 1), datetime(2023, 1, 1, 2)]
    result_ts = ts[dt_list]

    assert isinstance(result_ts, PQResult)
    assert len(result_ts.data) == 2
    assert result_ts.data.index[0] == dt_list[0]
    assert result_ts.data.index[1] == dt_list[1]


def test_get_list_of_datetimes_out_of_bounds_upper():
    ts = create_custom_pq_res()
    dt_list = [datetime(2023, 1, 1, 1), datetime(2023, 1, 2, 2)]
    result_ts = ts[dt_list]

    assert isinstance(result_ts, PQResult)
    assert len(result_ts.data) == 2
    assert result_ts.data.index[0] == dt_list[0]
    assert result_ts.data.index[1] == ts.data.index[-1]


def test_get_list_of_datetimes_out_of_bounds_lower():
    ts = create_custom_pq_res()
    dt_list = [datetime(2022, 1, 1, 1), datetime(2023, 1, 1, 2)]
    result_ts = ts[dt_list]

    assert isinstance(result_ts, PQResult)
    assert len(result_ts.data) == 2
    assert result_ts.data.index[0] == ts.data.index[0]
    assert result_ts.data.index[1] == dt_list[1]


def test_get_list_of_datetimes_out_of_bounds_both():
    ts = create_custom_pq_res()
    dt_list = [datetime(2022, 1, 1, 1), datetime(2023, 1, 2, 2)]
    result_ts = ts[dt_list]

    assert isinstance(result_ts, PQResult)
    assert len(result_ts.data) == 2
    assert result_ts.data.index[0] == ts.data.index[0]
    assert result_ts.data.index[1] == ts.data.index[-1]


def test_copy():
    ts = create_custom_pq_res()
    ts_copy = ts.copy()
    assert id(ts.data) != id(ts_copy.data)
    ts_copy = ts.copy(deep=False)
    assert id(ts.data) == id(ts_copy.data)
    empty_df = pd.DataFrame()
    ts_copy = ts.copy(**{"data": empty_df})
    ts_copy.data.equals(empty_df)
