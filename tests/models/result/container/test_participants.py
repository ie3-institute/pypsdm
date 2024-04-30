import pandas as pd

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.result.container.participants import (
    SystemParticipantsResultContainer,
)
from pypsdm.models.ts.base import TIME_COLUMN_NAME, EntityKey
from pypsdm.models.ts.types import ComplexPower, ComplexPowerWithSoc


def get_power_data(with_soc=False):
    data = pd.DataFrame(
        {
            TIME_COLUMN_NAME: [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
            ],
            "p": [0.0, 1.0, -2.0, 3.0],
            "q": [0.0, -1.0, 2.0, 3.0],
        },
    )
    if with_soc:
        data["soc"] = [0.0, 0.1, 0.2, 0.3]
        return ComplexPowerWithSoc(data)
    return ComplexPower(data)


def get_entities_dict(with_soc=False):
    dct = {
        EntityKey("a"): get_power_data(with_soc),
        EntityKey("b"): get_power_data(with_soc),
        EntityKey("c"): get_power_data(with_soc),
    }
    return dct


def get_container() -> SystemParticipantsResultContainer:
    dcts = {}
    for key in SystemParticipantsResultContainer.entity_keys():
        dict_type = key.get_result_dict_type()
        dcts[key] = dict_type(get_entities_dict(key.has_soc()))
    return SystemParticipantsResultContainer(dcts)


def test_from_csv(tmp_path):
    data_str = """
time,p,q,uuid,input_model
2021-01-01 00:00:00,0.0,0.0,a,a
2021-01-02 00:00:00,1.0,-1.0,a,a
2021-01-03 00:00:00,-2.0,2.0,a,a
2021-01-04 00:00:00,3.0,3.0,a,a
2021-01-01 00:00:00,0.0,0.0,b,b
2021-01-02 00:00:00,1.0,-1.0,b,b
2021-01-03 00:00:00,-2.0,2.0,b,b
2021-01-04 00:00:00,3.0,3.0,b,b
2021-01-01 00:00:00,0.0,0.0,c,c
2021-01-02 00:0:00,1.0,-1.0,c,c
2021-01-03 00:00:00,-2.0,2.0,c,c
2021-01-04 00:00:00,3.0,3.0,c,c
"""
    participants = (
        SystemParticipantsResultContainer({}).to_dict(include_empty=True).keys()
    )
    for participant in participants:
        file_path = tmp_path / participant.get_csv_result_file_name()
        with open(file_path, "w") as f:
            f.write(data_str)

    res = SystemParticipantsResultContainer.from_csv(tmp_path)
    res_dict = res.to_dict()
    for _, val in res_dict.items():
        assert set(val.data.keys()) == {EntityKey("a"), EntityKey("b"), EntityKey("c")}
        for ts in val.values():
            assert ts.data.shape == (4, 2)
    assert set(res_dict.keys()) == set(participants)


def test_to_csv(tmp_path):
    a = get_container()
    a.to_csv(tmp_path)
    b = SystemParticipantsResultContainer.from_csv(tmp_path)
    assert a == b


def test_participants_p():
    participants = get_container()
    participants_p = participants.p()
    names = {
        e.value
        for e in participants.entity_keys()
        if not e == SystemParticipantsEnum.FLEX_OPTIONS
    }
    assert set(participants_p.columns) == names


def test_participants_q():
    participants = get_container()
    participants_p = participants.q()
    names = {
        e.value
        for e in participants.entity_keys()
        if not e == SystemParticipantsEnum.FLEX_OPTIONS
    }
    assert set(participants_p.columns) == names


def test_participants_p_sum():
    participants = get_container()
    p_sum = participants.p_sum()
    assert p_sum.shape == (4,)


def test_participants_q_sum():
    participants = get_container()
    q_sum = participants.q_sum()
    assert q_sum.shape == (4,)
