import copy
import math
from datetime import datetime

import pytest

from pypsdm.models.gwr import GridWithResults


@pytest.fixture(scope="module")
def gwr(input_path_sb, result_path_sb) -> GridWithResults:
    return GridWithResults.from_csv(input_path_sb, result_path_sb)


@pytest.fixture
def node_uuid():
    return "32145578-706b-47e5-86ae-217d9a41867c"


def test_nodal_result(gwr: GridWithResults, node_uuid):
    nodal_res = gwr.nodal_result(node_uuid)
    assert len(nodal_res.nodes) == 1
    assert len(nodal_res.nodes)
    assert node_uuid in nodal_res.nodes
    assert len(nodal_res.participants.loads) == 1
    assert len(nodal_res.participants.fixed_feed_ins) == 1


def test_nodal_results(gwr: GridWithResults, node_uuid: str):
    nodal_results = gwr.nodal_results()
    assert len(nodal_results) == len(gwr.grid.raw_grid.nodes)
    a = nodal_results[node_uuid]
    b = gwr.nodal_result(node_uuid)
    assert a == b


def test_nodal_energies(gwr, node_uuid):
    nodal_energies = gwr.nodal_energies()
    assert nodal_energies[node_uuid] == gwr.nodal_energy(node_uuid)


def test_filter_by_date_time(gwr):
    dt = datetime(year=2016, month=1, day=2, hour=13, minute=30)
    filtered = gwr.filter_by_date_time(dt)
    assert isinstance(filtered, GridWithResults)
    assert len(filtered.loads_res.p()) == 1
    assert len(filtered.loads_res.q()) == 1


def test_compare(gwr: GridWithResults):
    gwr_2 = copy.deepcopy(gwr)
    gwr.compare(gwr_2)


def test_create_empty():
    empty = GridWithResults.empty()
    if empty:
        raise AssertionError("Empty GridWithResults should be falsy")


def test_to_csv(gwr: GridWithResults, tmp_path):
    gwr.to_csv(tmp_path, tmp_path, include_primary_data=True)
    gwr_b = GridWithResults.from_csv(
        tmp_path,
        tmp_path,
    )
    gwr.compare(gwr_b)
    assert gwr == gwr_b


def test_build_extended_nodes_result(gwr):
    ext_nodes_res = gwr.build_extended_nodes_result()
    assert len(ext_nodes_res) == len(gwr.nodes_res)

    # Compare sum of participants power at node with calculated node power
    for uuid in ext_nodes_res.keys():
        excluded = gwr.transformers_2_w.node.to_list()
        if uuid in excluded:
            continue

        expected = gwr.nodal_result(uuid).participants.sum().data.shift(1).iloc[1::]
        actual = ext_nodes_res[uuid].data.iloc[1::]
        if len(expected.p) == 0:
            assert math.isclose(actual.p.sum(), 0, rel_tol=1e-8)
            continue
        p_delta = (expected.p - actual.p).abs()
        assert (p_delta < 1e-8).all(), f"Unexpected deviation for {uuid}"
