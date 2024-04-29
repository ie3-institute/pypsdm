from copy import deepcopy

import pytest

from pypsdm.errors import ComparisonError
from pypsdm.models.input.container.raw_grid import RawGridContainer


@pytest.fixture(scope="module")
def raw_grid(input_path_sg) -> RawGridContainer:
    return RawGridContainer.from_csv(input_path_sg)


def test_raw_grid_container(raw_grid):
    assert len(raw_grid.lines) == 291
    assert len(raw_grid.nodes) == 299


def test_build_networkx_graph(raw_grid):
    G = raw_grid.build_networkx_graph()

    # all nodes and lines present
    assert len(G.nodes) == len(raw_grid.nodes)
    assert len(G.edges) == len(raw_grid.lines) + len(raw_grid.switches.get_closed())

    # correct line length in data dict
    for _, line in raw_grid.lines.data.iterrows():
        assert G.has_edge(line["node_a"], line["node_b"])
        assert G.edges[(line["node_a"], line["node_b"])]["weight"] == line["length"]


def test_create_empty():
    empty_container = RawGridContainer.empty()
    if empty_container:
        raise AssertionError("Empty container should be falsy")


def test_compare(raw_grid):
    raw_grid_b = deepcopy(raw_grid)

    assert raw_grid.compare(raw_grid_b) is None

    with pytest.raises(ComparisonError) as comp_exc:
        line_uuid = raw_grid.lines.uuid[0]
        raw_grid_b.lines.data.loc[line_uuid, "length"] = 42
        trafo_uuid = raw_grid.transformers_2_w.uuid[0]
        raw_grid_b.transformers_2_w.data.loc[trafo_uuid, "node_a"] = "I was changed.."
        raw_grid.compare(raw_grid_b)

    assert len(comp_exc.value.differences) == 2
