import datetime

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.result.participant.participants_res_container import (
    ParticipantsResultContainer,
)
from tests import utils

result_data = ParticipantsResultContainer.from_csv(
    utils.VN_SIMONA_RESULT_PATH,
    utils.VN_SIMONA_DELIMITER,
    datetime.datetime(year=2011, month=1, day=1, hour=15),
)


def test_energy():
    energy_dict = result_data.energies()
    assert len(energy_dict) == 7


# todo: update test data: since time stamps don't match its hard to do sensible energy comparisons
def test_participants_p():
    participants_p = result_data.p()
    assert SystemParticipantsEnum.LOAD.value in participants_p
    loads_p = participants_p[SystemParticipantsEnum.LOAD.value]
    # assert duration_weighted_sum(loads_p) == duration_weighted_sum(result_data.loads.p_sum())
    assert SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value in participants_p
    wecs_p = participants_p[SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value]
    # assert wecs_p.dropna().equals(result_data.wecs.p_sum())
    assert SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value in participants_p
    pvs_p = participants_p[SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value]
    # assert pvs_p.dropna().equals(result_data.pvs.p_sum())


def test_participants_q():
    participants_q = result_data.q()
    assert SystemParticipantsEnum.LOAD.value in participants_q
    loads_q = participants_q[SystemParticipantsEnum.LOAD.value]
    # assert loads_q.dropna().equals(result_data.loads.q_sum())
    assert SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value in participants_q
    wecs_q = participants_q[SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value]
    # assert wecs_q.dropna().equals(result_data.wecs.q_sum())
    assert SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value in participants_q
    pvs_q = participants_q[SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value]
    # assert pvs_q.dropna().equals(result_data.pvs.q_sum())


def test_p_sum():
    pv_sum = result_data.pvs.p_sum()
