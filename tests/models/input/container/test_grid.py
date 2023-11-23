import copy
import os
import os.path

from definitions import ROOT_DIR
from pypsdm.models.input.container.grid import GridContainer


def test_grid_container(gwr):
    grid_container = gwr.grid
    assert len(grid_container.raw_grid.lines) == 291
    assert len(grid_container.raw_grid.nodes) == 299
    assert len(grid_container.participants.loads) == 496


def test_node_participants_map(gwr):
    grid_container = gwr.grid
    node_participants = grid_container.node_participants_map[
        "401f37f8-6f2c-4564-bc78-6736cb9cbf8d"
    ]
    assert len(node_participants.wecs) == 1
    assert len(node_participants.loads) == 1
    assert len(node_participants.biomass_plants) == 0


def test_create_empty():
    empty_container = GridContainer.create_empty()
    if empty_container:
        raise AssertionError("Empty container should be falsy")


def test_container_to_csv(gwr):
    grid_container = gwr.grid
    path = os.path.join(ROOT_DIR, "tests", "temp", "grid")
    os.makedirs(path, exist_ok=True)
    grid_container.to_csv(path, include_primary_data=False)


def test_compare(gwr):
    grid_a = gwr.grid
    grid_b = copy.deepcopy(grid_a)
    assert grid_a.compare(grid_b) is None
