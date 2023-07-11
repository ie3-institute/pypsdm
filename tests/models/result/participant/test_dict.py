from datetime import datetime

import pandas as pd
from pytest import fixture

from psdm_analysis.models.enums import SystemParticipantsEnum
from psdm_analysis.models.result.participant.participant import ParticipantsResult
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


@fixture
def res_dict():
    # def create_res_dict():
    start = datetime(2023, 1, 1)
    periods = 5
    data = create_sample_data(start, periods)
    a = PQResult(SystemParticipantsEnum.LOAD, "test-res-a", "test-res-a", data)
    b = PQResult(SystemParticipantsEnum.LOAD, "test-res-a", "test-res-a", data * 2)
    return ParticipantsResult(SystemParticipantsEnum.LOAD, {"a": a, "b": b})


def test_add(res_dict):
    start = datetime(2023, 1, 1)
    periods = 5
    data = create_sample_data(start, periods)
    c = PQResult(SystemParticipantsEnum.LOAD, "test-res-c", "test-res-c", data)
    res_dict_b = ParticipantsResult(SystemParticipantsEnum.LOAD, {"c": c})
    added = res_dict + res_dict_b
    assert len(added) == 3
    assert list(added.entities.keys()) == ["a", "b", "c"]

    # test with key already in dict
    res_dict_c = res_dict.subset(["b"])
    added = res_dict + res_dict_c
    assert len(added) == 2
    assert list(added.entities.keys()) == ["a", "b"]


def test_sub(res_dict):
    res_dict_b = res_dict.subset(["b"])
    sub = res_dict - res_dict_b
    assert len(sub) == 1
    assert list(sub.entities.keys()) == ["a"]
