import os.path

from definitions import ROOT_DIR


def test_node_participants_map(gwr):
    grid_container = gwr.grid
    node_participants = grid_container.node_participants_map[
        "401f37f8-6f2c-4564-bc78-6736cb9cbf8d"
    ]
    assert len(node_participants.wecs) == 1
    assert len(node_participants.loads) == 1
    assert len(node_participants.biomass_plants) == 0


def test_container_to_csv(gwr, delimiter):
    grid_container = gwr.grid
    path = os.path.join(ROOT_DIR, "tests", "temp", "grid")
    os.makedirs(path, exist_ok=True)
    grid_container.to_csv(path, delimiter)