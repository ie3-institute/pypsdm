from psdm_analysis.models.input.container.participants_container import (
    SystemParticipantsContainer,
)
from tests import utils
from tests.utils import VN_SIMONA_DELIMITER, VN_SIMONA_INPUT_PATH

participants = SystemParticipantsContainer.from_csv(
    VN_SIMONA_INPUT_PATH, VN_SIMONA_DELIMITER
)


def test_spa_container_from_csv():
    assert len(participants.loads) == 496
    assert len(participants.pvs) == 63
    assert len(participants.biomass_plants) == 1
    assert len(participants.wecs) == 2


def test_filter_by_node():
    filtered = participants.filter_by_node("401f37f8-6f2c-4564-bc78-6736cb9cbf8d")
    assert len(filtered.wecs) == 1
    assert len(filtered.loads) == 1
    assert len(filtered.biomass_plants) == 0


def test_empty_participants():
    empty_participants = SystemParticipantsContainer.from_csv(
        utils.EMPTY_GRID_PATH, ","
    )
    assert len(empty_participants.biomass_plants) == 0


test_filter_by_node()
