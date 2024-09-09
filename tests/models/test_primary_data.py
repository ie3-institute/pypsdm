import uuid

import pandas as pd

from pypsdm.errors import ComparisonError
from pypsdm.models.enums import TimeSeriesEnum
from pypsdm.models.primary_data import PrimaryData, TimeSeriesKey
from pypsdm.models.ts.base import TIME_COLUMN_NAME
from pypsdm.models.ts.types import ComplexPower, ComplexPowerDict


def get_sample_data(q: bool = True, h: bool = False):
    data = pd.DataFrame(
        {
            TIME_COLUMN_NAME: [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
            ],
            "p": [0.0, 1.0, -2.0, 3.0],
        },
    )
    if q:
        data["q"] = [0.0, -1.0, 2.0, 3.0]
    else:
        data["q"] = [0.0, 0.0, 0.0, 0.0]
    if h:
        data["h"] = [0.0, -1.0, 2.0, 3.0]
    return ComplexPower(data)


def get_power_dict():
    dct = {
        TimeSeriesKey("a", TimeSeriesEnum.PQ_TIME_SERIES): get_sample_data(),
        TimeSeriesKey("b", TimeSeriesEnum.P_TIME_SERIES): get_sample_data(q=False),
        TimeSeriesKey("c", TimeSeriesEnum.PQH_TIME_SERIES): get_sample_data(h=True),
    }
    return ComplexPowerDict(dct)


def get_primary_data():
    ts = get_power_dict()
    participant_mapping = {
        "p_a": "a",
        "p_b": "b",
        "p_c": "c",
    }
    return PrimaryData(ts, participant_mapping)


def test_key():
    dct = get_power_dict()
    key = TimeSeriesKey("a", TimeSeriesEnum.PQ_TIME_SERIES)
    assert key in dct
    key = TimeSeriesKey("a", None)
    assert key in dct


def test_getitem():
    pd = get_primary_data()
    assert pd["a"] == pd[TimeSeriesKey("a", TimeSeriesEnum.PQ_TIME_SERIES)]
    assert pd["p_a"] == pd["a"]


def test_filter_by_participants():
    pd = get_primary_data()
    res = pd.filter_by_participants(["p_a", "p_b"])
    assert len(res) == 2
    assert "a" in res
    assert "b" in res
    assert "c" not in res


def test_compare():
    pd = get_primary_data()
    pd2 = get_primary_data()
    pd.compare(pd2)
    pd2._time_series[TimeSeriesKey("a", TimeSeriesEnum.P_TIME_SERIES)] = (
        get_sample_data(q=False)
    )
    try:
        pd.compare(pd2)
        assert False
    except ComparisonError:
        assert True


def test_to_csv(tmp_path):
    pd = get_primary_data()
    uuid_ts = {}
    for key, ts in pd._time_series.items():
        ts_uuid = uuid.uuid4()
        key = TimeSeriesKey(str(ts_uuid), key.ts_type)
        uuid_ts[key] = ts
    pd._time_series = ComplexPowerDict(uuid_ts)
    pd.to_csv(tmp_path)
    pd2 = PrimaryData.from_csv(tmp_path)
    assert pd == pd2
