import os

import pytest

from definitions import ROOT_DIR
from psdm_analysis.models.input.container.participants_container import (
    SystemParticipantsContainer,
)


@pytest.fixture(scope="module")
def participants(gwr):
    return gwr.grid.participants


def test_spa_container_from_csv(participants):
    assert len(participants.loads) == 496
    assert len(participants.pvs) == 63
    assert len(participants.biomass_plants) == 1
    assert len(participants.wecs) == 2


def test_filter_by_node(participants):
    filtered = participants.filter_by_node("401f37f8-6f2c-4564-bc78-6736cb9cbf8d")
    assert len(filtered.wecs) == 1
    assert len(filtered.loads) == 1
    assert len(filtered.biomass_plants) == 0


def test_empty_participants(participants):
    empty_grid_path = os.path.join(ROOT_DIR, "tests", "resources", "empty_grid")
    empty_participants = SystemParticipantsContainer.from_csv(empty_grid_path, ",")
    assert len(empty_participants.biomass_plants) == 0