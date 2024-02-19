from copy import deepcopy

import pytest

from pypsdm.errors import ComparisonError
from pypsdm.models.gwr import GridWithResults
from pypsdm.models.input.container.raw_grid import RawGridContainer


def test_raw_grid_container(gwr):
    raw_grid_container = gwr.grid.raw_grid
    assert len(raw_grid_container.lines) == 291
    assert len(raw_grid_container.nodes) == 299


def test_build_networkx_graph(gwr: GridWithResults):
    G = gwr.grid.raw_grid.build_networkx_graph()

    # all nodes and lines present
    assert len(G.nodes) == len(gwr.grid.raw_grid.nodes)
    assert len(G.edges) == len(gwr.grid.raw_grid.lines) + len(
        gwr.grid.raw_grid.switches.get_closed()
    )

    # correct line length in data dict
    for _, line in gwr.grid.raw_grid.lines.data.iterrows():
        assert G.has_edge(line["node_a"], line["node_b"])
        assert G.edges[(line["node_a"], line["node_b"])]["weight"] == line["length"]


def test_create_empty():
    empty_container = RawGridContainer.create_empty()
    if empty_container:
        raise AssertionError("Empty container should be falsy")


def test_compare(gwr: GridWithResults):
    raw_grid_container = gwr.grid.raw_grid
    raw_grid_container_b = deepcopy(raw_grid_container)

    assert raw_grid_container.compare(raw_grid_container_b) is None

    with pytest.raises(ComparisonError) as comp_exc:
        line_uuid = raw_grid_container.lines.uuid[0]
        raw_grid_container_b.lines.data.loc[line_uuid, "length"] = 42
        trafo_uuid = raw_grid_container.transformers_2_w.uuid[0]
        raw_grid_container_b.transformers_2_w.data.loc[trafo_uuid, "node_a"] = (
            "I was changed.."
        )
        raw_grid_container.compare(raw_grid_container_b)

    assert len(comp_exc.value.differences) == 2
