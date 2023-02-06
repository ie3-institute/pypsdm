import functools
import os
from datetime import datetime

import pandas as pd

from psdm_analysis.io.utils import get_absolute_path
from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.result.participant.participant import ParticipantsResult
from psdm_analysis.models.result.power import PQResult
from psdm_analysis.processing.series import duration_weighted_series
from tests import utils
from tests.utils import is_close

wec_results = ParticipantsResult.from_csv(
    SystemParticipantsEnum.WIND_ENERGY_CONVERTER,
    utils.VN_SIMONA_RESULT_PATH,
    utils.VN_SIMONA_DELIMITER,
    utils.VN_SIMULATION_END,
)
wec_a_uuid = "f9eaec6e-ce25-42d7-8265-2f8f4679a816"
wec_b_uuid = "d6ad8c73-716a-4244-9ae2-4a3735e492ab"
assert wec_a_uuid in wec_results.participants.keys()
assert wec_b_uuid in wec_results.participants.keys()
wec_a = wec_results.get(wec_a_uuid)
wec_b = wec_results.get(wec_b_uuid)


def test_p():
    p = wec_results.p()
    assert len(p) == 4
    assert len(p.columns) == 2
    assert is_close(p.sum()[wec_a_uuid], -0.9)


def test_q():
    q = wec_results.q()
    assert len(q) == 4
    assert len(q.columns) == 2
    assert is_close(q.sum()[wec_a_uuid], -0.6)


def test_p_sum():
    p = wec_results.p()
    p_sum = wec_results.p_sum()
    now = datetime(2011, 1, 1, 13, 30)
    previous = datetime(2011, 1, 1, 13, 0)
    assert len(p_sum) == 4
    assert p_sum[now] == p[wec_a_uuid][now] + p[wec_b_uuid][previous]


def test_q_sum():
    q = wec_results.q()
    q_sum = wec_results.q_sum()
    now = datetime(2011, 1, 1, 13, 30)
    previous = datetime(2011, 1, 1, 13, 0)
    assert len(q_sum) == 4
    assert q_sum[now] == q[wec_a_uuid][now] + q[wec_b_uuid][previous]


# todo adjust to updated power values
def test_filter_for_time_interval():
    start = datetime(2011, 1, 1, 13, 30)
    end = datetime(2011, 1, 1, 14, 0)
    filtered = wec_results.filter_for_time_interval(start, end)
    assert len(filtered.participants.keys()) == 2
    filtered_wec_a = filtered.get(wec_a_uuid)
    filtered_wec_b = filtered.get(wec_b_uuid)
    assert len(filtered_wec_a.data) == 2
    assert len(filtered_wec_b.data) == 2
    assert filtered_wec_a.data.iloc[0].name == start
    assert is_close(filtered_wec_a.p()[start], -0.3)
    assert is_close(filtered_wec_a.q()[start], -0.2)
    assert filtered_wec_b.data.iloc[0].name == start
    assert is_close(filtered_wec_b.p()[start], -0.3)
    assert is_close(filtered_wec_b.q()[start], -0.2)


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


def test_energy():
    actual = wec_a.energy()
    dt_a = datetime(2011, 1, 1, 12, 0)
    dt_b = datetime(2011, 1, 1, 13, 30)
    expected = wec_a.p()[dt_a] * 1.5 + wec_a.p()[dt_b] * 0.5
    assert is_close(actual, expected)


def test_duration_weighted_series():
    duration_weighted_series(wec_a.p())


def test_add():
    res = wec_a + wec_b
    assert is_close(res.energy(), wec_a.energy() + wec_b.energy())


def test_sum_add():
    res = PQResult.sum([wec_a, wec_b])
    sum = wec_a + wec_b
    assert (res.p() == sum.p()).all()
    assert (res.q() == sum.q()).all()


def test_drop_non_unique_time_stamp():
    ffi_results = ParticipantsResult.from_csv(
        SystemParticipantsEnum.FIXED_FEED_IN,
        utils.VN_SIMONA_RESULT_PATH,
        utils.VN_SIMONA_DELIMITER,
        utils.VN_SIMULATION_END,
    ).get("9abe950d-362e-4efe-b686-500f84d8f368")
    assert ffi_results.data.iloc[0]["p"] == -0.3


def test_subset():
    wec_subset = wec_results.subset([wec_a_uuid, "no_uuid"])
    assert len(wec_subset) == 1


def test_to_csv():
    output_dir = os.path.join(get_absolute_path("tests"), "temp")
    os.makedirs(output_dir, exist_ok=True)
    wec_a.to_csv(output_dir)


def test_from_csv():
    output_dir = os.path.join(get_absolute_path("tests"), "temp")
    os.makedirs(output_dir, exist_ok=True)
    wec_a.to_csv(output_dir)
    file_name = wec_a.get_default_output_name()
    res = PQResult.from_csv(os.path.join(output_dir, file_name), wec_a.type)
    assert (res.p() == wec_a.p()).all()
    assert (res.q() == wec_a.q()).all()
