import copy

import pytest

from pypsdm.models.input.container.grid import GridContainer


@pytest.fixture(scope="module")
def grid_container(input_path_sg) -> GridContainer:
    return GridContainer.from_csv(input_path_sg)


def test_grid_container(grid_container: GridContainer):
    assert len(grid_container.raw_grid.lines) == 3
    assert len(grid_container.raw_grid.nodes) == 5
    assert len(grid_container.participants.loads) == 3
    assert len(grid_container.transformers_2_w) == 1


def test_node_participants_map(grid_container: GridContainer):
    node_participants = grid_container.node_participants_map[
        "b7a5be0d-2662-41b2-99c6-3b8121a75e9e"
    ]
    assert len(node_participants.loads) == 1
    assert len(node_participants.controlling_ems) == 1
    assert len(node_participants.pvs) == 1


def test_create_empty():
    empty_container = GridContainer.empty()
    if empty_container:
        raise AssertionError("Empty container should be falsy")


def test_container_to_csv(tmp_path, grid_container: GridContainer):
    grid_container.to_csv(tmp_path, include_primary_data=False)
    grid_container_b = GridContainer.from_csv(tmp_path)
    assert grid_container == grid_container_b


def test_compare(grid_container):
    grid_a = grid_container
    grid_b = copy.deepcopy(grid_a)
    grid_a.compare(grid_b)
    assert grid_a == grid_b
