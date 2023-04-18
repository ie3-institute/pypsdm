import datetime
import math

import pytest

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.processing.series import duration_weighted_sum


@pytest.fixture
def participants_results(gwr):
    return gwr.results.participants


def test_energy(participants_results):
    energy_dict = participants_results.energies()
    assert len(energy_dict) == 7


def compare_duration_weighted_sum(a, b):
    a_res = duration_weighted_sum(a)
    b_res = duration_weighted_sum(b)
    assert math.isclose(a_res, b_res, rel_tol=1e-6)


def test_participants_p(participants_results):
    participants_p = participants_results.p
    assert SystemParticipantsEnum.LOAD.value in participants_p
    loads_p = participants_p[SystemParticipantsEnum.LOAD.value]
    compare_duration_weighted_sum(loads_p, participants_results.loads.p_sum())
    assert SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value in participants_p
    wecs_p = participants_p[SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value]
    compare_duration_weighted_sum(wecs_p, participants_results.wecs.p_sum())
    assert SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value in participants_p
    pvs_p = participants_p[SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value]
    compare_duration_weighted_sum(pvs_p, participants_results.pvs.p_sum())


def test_participants_p_sum(participants_results):
    p_sum = participants_results.p_sum()
    dt = datetime.datetime(year=2011, month=1, day=1, hour=14)
    assert math.isclose(
        p_sum[dt].sum(), sum([177.89953, -0.4, -0.8, -1.01849]), rel_tol=1e-5
    )


def test_participants_q(participants_results):
    participants_q = participants_results.q
    assert SystemParticipantsEnum.LOAD.value in participants_q
    loads_q = participants_q[SystemParticipantsEnum.LOAD.value]
    compare_duration_weighted_sum(loads_q, participants_results.loads.q_sum())
    assert SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value in participants_q
    wecs_q = participants_q[SystemParticipantsEnum.WIND_ENERGY_CONVERTER.value]
    compare_duration_weighted_sum(wecs_q, participants_results.wecs.q_sum())
    assert SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value in participants_q
    pvs_q = participants_q[SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT.value]
    compare_duration_weighted_sum(pvs_q, participants_results.pvs.q_sum())
