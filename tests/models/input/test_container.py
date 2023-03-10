import os.path

from definitions import ROOT_DIR
from psdm_analysis.models.input.container.grid_container import GridContainer
from tests import utils

grid_container = GridContainer.from_csv(
    utils.VN_SIMONA_INPUT_PATH, utils.VN_SIMONA_DELIMITER
)


def test_node_participants_map():
    node_participants = grid_container.node_participants_map[
        "401f37f8-6f2c-4564-bc78-6736cb9cbf8d"
    ]
    assert len(node_participants.wecs) == 1
    assert len(node_participants.loads) == 1
    assert len(node_participants.biomass_plants) == 0


def test_container_to_csv():
    path = os.path.join(ROOT_DIR, "tests", "temp", "grid")
    os.makedirs(path, exist_ok=True)
    grid_container.to_csv(path, utils.VN_SIMONA_DELIMITER)
