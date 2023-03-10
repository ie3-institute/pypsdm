import os

import pytest

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.wec import WindEnergyConverters
from tests.utils import compare_dfs


@pytest.fixture(scope="module")
def wecs(gwr) -> WindEnergyConverters:
    return gwr.grid.participants.wecs

def test_sp_enum():
    bm = SystemParticipantsEnum.BIOMASS_PLANT
    pv = SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT
    assert bm.has_type() is True
    assert pv.has_type() is False


def test_filter_for_node(wecs):
    filtered = wecs.filter_for_node("401f37f8-6f2c-4564-bc78-6736cb9cbf8d")
    assert len(filtered) == 1


def test_subset(wecs):
    subset = wecs.subset(["d6ad8c73-716a-4244-9ae2-4a3735e492ab", "not_in_df"])
    assert len(subset) == 1


def test_to_csv(wecs, delimiter, tmp_path):
    path = os.path.join(tmp_path, "wecs")
    os.makedirs(path, exist_ok=True)
    wecs.to_csv(path, delimiter)
    wecs2 = WindEnergyConverters.from_csv(path, delimiter)
    # todo this needs to be tested for other participants
    compare_dfs(wecs.data, wecs2.data)