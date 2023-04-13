import datetime
import math

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.result.participant.participants_res_container import (
    ParticipantsResultContainer,
)
from psdm_analysis.processing.series import duration_weighted_sum
from tests import utils

result_data = ParticipantsResultContainer.from_csv(
    utils.VN_SIMONA_RESULT_PATH,
    utils.VN_SIMONA_DELIMITER,
    datetime.datetime(year=2012, month=2, day=3, hour=4, minute=15),
)


def test_energy():
    energy_dict = result_data.energies()
    assert len(energy_dict) == 7


def compare_duration_weighted_sum(a, b):
    a_res = duration_weighted_sum(a)
    b_res = duration_weighted_sum(b)
    assert math.isclose(
        a_res, b_res, rel_tol=1e-6
    )


def test_participants_p():
    participants_p = result_data.p
    assert SystemParticipantsEnum.LOAD.value in participants_p
    loads_p = participants_p[SystemParticipantsEnum.LOAD.value]
    compare_duration_weighted_sum(loads_p, result_data.loads.p_sum())
    assert SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value in participants_p
    wecs_p = participants_p[SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value]
    compare_duration_weighted_sum(wecs_p, result_data.wecs.p_sum())
    assert SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value in participants_p
    pvs_p = participants_p[SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value]
    compare_duration_weighted_sum(pvs_p, result_data.pvs.p_sum())


def test_participants_p_sum():
    p_sum = result_data.p_sum()
    dt = datetime.datetime(year=2011, month=1, day=1, hour=14)
    assert math.isclose(
        p_sum[dt].sum(), sum([177.89953, -0.4, -0.8, -1.01849]), rel_tol=1e-5
    )


def test_participants_q():
    participants_q = result_data.q
    assert SystemParticipantsEnum.LOAD.value in participants_q
    loads_q = participants_q[SystemParticipantsEnum.LOAD.value]
    compare_duration_weighted_sum(loads_q, result_data.loads.q_sum())
    assert SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value in participants_q
    wecs_q = participants_q[SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value]
    compare_duration_weighted_sum(wecs_q, result_data.wecs.q_sum())
    assert SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value in participants_q
    pvs_q = participants_q[SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value]
    compare_duration_weighted_sum(pvs_q, result_data.pvs.q_sum())
