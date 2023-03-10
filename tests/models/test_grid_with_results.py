import pytest

from psdm_analysis.models.result.grid.enhanced_node import EnhancedNodeResult

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
    assert nodal_results[node_uuid] == gwr.nodal_result(
        node_uuid
    )


def test_nodal_energies(gwr, node_uuid):
    nodal_energies = gwr.nodal_energies()
    assert nodal_energies[node_uuid] == gwr.nodal_energy(
        node_uuid
    )


def test_build_enhanced_nodes_result(gwr, node_uuid):
    enhanced_node_results = gwr.build_enhanced_nodes_result()
    assert len(enhanced_node_results) == 299
    node_res = gwr.nodal_result(node_uuid)
    p = node_res.participants.sum().p
    q = node_res.participants.sum().q
    expected = EnhancedNodeResult.from_node_result(
        node_res.nodes.entities[node_uuid], p, q
    )
    assert enhanced_node_results.entities[node_uuid] == expected
