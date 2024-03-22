import copy
import math
import os
from datetime import datetime

import pytest

from pypsdm.models.gwr import GridWithResults


@pytest.fixture
def node_uuid():
    return "401f37f8-6f2c-4564-bc78-6736cb9cbf8d"


def test_nodal_result(gwr, node_uuid):
    nodal_res = gwr.nodal_result(node_uuid)
    assert len(nodal_res.nodes) == 1
    assert len(nodal_res.nodes)
    assert node_uuid in nodal_res.nodes.entities
    assert len(nodal_res.participants.wecs) == 1
    assert len(nodal_res.participants.loads) == 1
    assert len(nodal_res.participants.pvs) == 0


def test_nodal_results(gwr, node_uuid):
    nodal_results = gwr.nodal_results()
    assert len(nodal_results) == len(gwr.grid.raw_grid.nodes)
    assert nodal_results[node_uuid] == gwr.nodal_result(node_uuid)


def test_nodal_energies(gwr, node_uuid):
    nodal_energies = gwr.nodal_energies()
    assert nodal_energies[node_uuid] == gwr.nodal_energy(node_uuid)


def test_filter_by_date_time(gwr):
    dt = datetime(year=2011, month=1, day=1, hour=13, minute=30)
    filtered = gwr.filter_by_date_time(dt)
    assert isinstance(filtered, GridWithResults)
    assert len(list(filtered.grid.primary_data.time_series.entities.values())[0]) == 1
    assert len(filtered.results.participants.pvs.results()[0]) == 1


def test_compare(gwr: GridWithResults):
    gwr_2 = copy.deepcopy(gwr)
    gwr.compare(gwr_2)


def test_create_empty():
    empty = GridWithResults.create_empty()
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


def test_build_extended_nodes_result(resources_path):
    sb_input = os.path.join(resources_path, "simbench", "input")
    sb_results = os.path.join(resources_path, "simbench", "results")
    gwr = GridWithResults.from_csv(sb_input, sb_results)
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
        p_delta = expected.p - actual.p
        assert (p_delta < 1e-8).all(), f"Unexpected deviation for {uuid}"
