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
        "p_a": TimeSeriesKey("a", TimeSeriesEnum.PQ_TIME_SERIES),
        "p_b": TimeSeriesKey("b", TimeSeriesEnum.P_TIME_SERIES),
        "p_c": TimeSeriesKey("c", TimeSeriesEnum.PQH_TIME_SERIES),
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
    res = pd.filter_by_assets(["p_a", "p_b"])
    assert len(res) == 2
    assert "a" in res
    assert "b" in res
    assert "c" not in res


def test_filter_by_assets():
    """Test filter_by_assets with various scenarios to ensure TimeSeriesKey mapping works correctly"""
    pd = get_primary_data()

    # Test 1: Filter by single asset
    res = pd.filter_by_assets(["p_a"])
    assert len(res) == 1
    assert "p_a" in res._asset_mapping
    assert res._asset_mapping["p_a"].ts_uuid == "a"
    assert res._asset_mapping["p_a"].ts_type == TimeSeriesEnum.PQ_TIME_SERIES

    # Test 2: Filter by multiple assets
    res = pd.filter_by_assets(["p_a", "p_c"])
    assert len(res) == 2
    assert "p_a" in res._asset_mapping
    assert "p_c" in res._asset_mapping
    assert "p_b" not in res._asset_mapping

    # Verify the TimeSeriesKey objects are preserved correctly
    assert res._asset_mapping["p_a"].ts_uuid == "a"
    assert res._asset_mapping["p_a"].ts_type == TimeSeriesEnum.PQ_TIME_SERIES
    assert res._asset_mapping["p_c"].ts_uuid == "c"
    assert res._asset_mapping["p_c"].ts_type == TimeSeriesEnum.PQH_TIME_SERIES

    # Test 3: Verify filtered time series contain correct keys
    filtered_ts_keys = set(res._time_series.keys())
    expected_keys = {
        TimeSeriesKey("a", TimeSeriesEnum.PQ_TIME_SERIES),
        TimeSeriesKey("c", TimeSeriesEnum.PQH_TIME_SERIES),
    }
    assert filtered_ts_keys == expected_keys

    # Test 4: Verify data integrity - filtered data should match original
    assert res["p_a"].data.equals(pd["p_a"].data)
    assert res["p_c"].data.equals(pd["p_c"].data)

    # Test 5: Test with skip_missing=True
    res_skip = pd.filter_by_assets(["p_a", "nonexistent"], skip_missing=True)
    assert len(res_skip) == 1
    assert "p_a" in res_skip._asset_mapping

    # Test 6: Test with skip_missing=False (default) should raise KeyError
    try:
        pd.filter_by_assets(["p_a", "nonexistent"])
        assert False, "Should have raised KeyError"
    except KeyError as e:
        assert "nonexistent" in str(e)

    # Test 7: Test empty filter
    res_empty = pd.filter_by_assets([])
    assert len(res_empty) == 0
    assert len(res_empty._asset_mapping) == 0


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
    asset_mapping = {}
    for key, ts in pd._time_series.items():
        ts_uuid = uuid.uuid4()
        new_key = TimeSeriesKey(str(ts_uuid), key.ts_type)
        uuid_ts[new_key] = ts
        # Update asset mapping to use the new key
        for asset, old_key in pd._asset_mapping.items():
            if old_key.ts_uuid == key.ts_uuid:
                asset_mapping[asset] = new_key
    pd._time_series = ComplexPowerDict(uuid_ts)
    pd._asset_mapping = asset_mapping
    pd.to_csv(tmp_path)
    pd2 = PrimaryData.from_csv(tmp_path)
    assert pd == pd2
