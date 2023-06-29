import os

import pytest

from psdm_analysis.models.input.participant.wec import WindEnergyConverters
from tests.utils import compare_dfs


@pytest.fixture(scope="module")
def wecs(gwr) -> WindEnergyConverters:
    return gwr.grid.participants.wecs


def test_filter_for_node(wecs):
    filtered = wecs.filter_by_nodes("401f37f8-6f2c-4564-bc78-6736cb9cbf8d")
    assert len(filtered) == 1


def test_to_csv(wecs, delimiter, tmp_path):
    path = os.path.join(tmp_path, "wecs")
    os.makedirs(path, exist_ok=True)
    wecs.to_csv(path, delimiter)
    wecs2 = WindEnergyConverters.from_csv(path, delimiter)
    # todo this needs to be tested for other participants
    compare_dfs(wecs.data, wecs2.data)
