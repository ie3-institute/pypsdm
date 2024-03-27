import functools
import os
from datetime import datetime

import pandas as pd
import pytest

from pypsdm.io.utils import get_absolute_path_from_project_root
from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.result.participant.pq_dict import PQResultDict
from pypsdm.models.result.power import PQResult
from pypsdm.processing.series import duration_weighted_series
from tests.utils import is_close


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


# TODO: Replace from csv tests with sample_data tests
@pytest.fixture
def wec_results(result_path):
    simulation_end = datetime(year=2011, month=1, day=1, hour=14)
    wecs = PQResultDict.from_csv(
        SystemParticipantsEnum.WIND_ENERGY_CONVERTER,
        result_path,
        simulation_end=simulation_end,
    )
    return wecs


wec_a_uuid = "f9eaec6e-ce25-42d7-8265-2f8f4679a816"
wec_b_uuid = "d6ad8c73-716a-4244-9ae2-4a3735e492ab"


@pytest.fixture
def wec_a(wec_results):
    assert wec_a_uuid in wec_results
    return wec_results.get(wec_a_uuid)


@pytest.fixture
def wec_b(wec_results):
    assert wec_b_uuid in wec_results
    return wec_results.get(wec_b_uuid)


def test_p(wec_results):
    p = wec_results.p()
    assert len(p) == 4
    assert len(p.columns) == 2
    assert is_close(p.sum()[wec_a_uuid], -1.1)


def test_q(wec_results):
    q = wec_results.q()
    assert len(q) == 4
    assert len(q.columns) == 2
    assert is_close(q.sum()[wec_a_uuid], -0.7)


def test_p_sum(wec_results):
    p = wec_results.p()
    p_sum = wec_results.p_sum()
    now = datetime(2011, 1, 1, 13, 30)
    previous = datetime(2011, 1, 1, 13, 0)
    assert len(p_sum) == 4
    assert p_sum[now] == p[wec_a_uuid][now] + p[wec_b_uuid][previous]


def test_q_sum(wec_results):
    q = wec_results.q()
    q_sum = wec_results.q_sum()
    now = datetime(2011, 1, 1, 13, 30)
    previous = datetime(2011, 1, 1, 13, 0)
    assert len(q_sum) == 4
    assert q_sum[now] == q[wec_a_uuid][now] + q[wec_b_uuid][previous]


def test_filter_for_time_interval(wec_results):
    start = datetime(2011, 1, 1, 13, 30)
    end = datetime(2011, 1, 1, 14, 0)
    filtered = wec_results.filter_for_time_interval(start, end)
    assert len(filtered.keys()) == 2
    filtered_wec_a = filtered.get(wec_a_uuid)
    filtered_wec_b = filtered.get(wec_b_uuid)
    assert len(filtered_wec_a.data) == 2
    assert len(filtered_wec_b.data) == 2
    assert filtered_wec_a.data.iloc[0].name == start
    assert is_close(filtered_wec_a.p[start], -0.3)
    assert is_close(filtered_wec_a.q[start], -0.2)
    assert filtered_wec_b.data.iloc[0].name == start
    assert is_close(filtered_wec_b.p[start], -0.3)
    assert is_close(filtered_wec_b.q[start], -0.2)


def test_filter_data_for_time_interval_non_overlapping():
    start = datetime(year=2022, month=12, day=1, hour=0)
    end = datetime(year=2022, month=12, day=1, hour=4)

    pq_partial = functools.partial(
        PQResult, SystemParticipantsEnum.LOAD, "test-res", "test-res"
    )

    index_after = pd.date_range("2022-12-01 04:00:00", "2022-12-01 06:00:00", freq="1h")
    data_after = pd.DataFrame(data={"p": [1, 2, 3], "q": [1, 2, 3]}, index=index_after)
    pq_res_after = pq_partial(data_after)
    filtered_after = pq_res_after.filter_for_time_interval(start, end)
    assert filtered_after.data.empty


def test_energy(wec_a):
    actual = wec_a.energy()
    dt_a = datetime(2011, 1, 1, 12, 0)
    dt_b = datetime(2011, 1, 1, 13, 30)
    expected = wec_a.p[dt_a] * 1.5 + wec_a.p[dt_b] * 0.5
    assert is_close(actual, expected)


def test_duration_weighted_series(wec_a):
    duration_weighted_series(wec_a.p)


def test_add(wec_a, wec_b):
    res = wec_a + wec_b
    assert is_close(res.energy(), wec_a.energy() + wec_b.energy())


def test_sum_add(wec_a, wec_b):
    res = PQResult.sum([wec_a, wec_b])
    sum = wec_a + wec_b
    assert (res.p == sum.p).all()
    assert (res.q == sum.q).all()


def test_drop_non_unique_time_stamp(gwr):
    ffis = gwr.results.participants.fixed_feed_ins
    ffi_result = ffis.get("9abe950d-362e-4efe-b686-500f84d8f368")
    assert ffi_result.data.iloc[0]["p"] == -0.3


def test_subset(wec_results):
    wec_subset = wec_results.subset([wec_a_uuid, "no_uuid"])
    assert len(wec_subset) == 1


def test_from_csv(wec_a):
    output_dir = os.path.join(get_absolute_path_from_project_root("tests"), "temp")
    os.makedirs(output_dir, exist_ok=True)
    wec_a.to_csv(output_dir)
    file_name = wec_a.get_default_output_name()
    res = PQResult.from_csv(os.path.join(output_dir, file_name), wec_a.entity_type)
    assert (res.p == wec_a.p).all()
    assert (res.q == wec_a.q).all()


def test_to_csv(tmpdir):
    ts_a = create_custom_pq_res()
    file_name = "pq_res.csv"
    ts_a.to_csv(tmpdir, file_name)
    file_path = os.path.join(tmpdir, file_name)
    ts_b = PQResult.from_csv(file_path, ts_a.entity_type, ts_a.name)
    ts_a.compare(ts_b)
