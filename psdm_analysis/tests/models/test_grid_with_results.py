from psdm_analysis.models.grid_with_results import GridWithResults
from psdm_analysis.models.result.grid.enhanced_node import EnhancedNodeResult
from tests import utils

grid = GridWithResults.from_csv(
    "vn_simona",
    utils.VN_SIMONA_INPUT_PATH,
    utils.VN_SIMONA_DELIMITER,
    utils.VN_SIMONA_RESULT_PATH,
    utils.VN_SIMONA_DELIMITER,
    utils.VN_SIMULATION_END,
)


def test_nodal_result():
    nodal_res = grid.nodal_result(utils.TEST_NODE_UUID)
    assert len(nodal_res.nodes) == 1
    assert len(nodal_res.nodes)
    assert utils.TEST_NODE_UUID in nodal_res.nodes.nodes
    assert len(nodal_res.participants.wecs) == 1
    assert len(nodal_res.participants.loads) == 1
    assert len(nodal_res.participants.pvs) == 0


def test_nodal_results():
    nodal_results = grid.nodal_results()
    assert len(nodal_results) == len(grid.grid.raw_grid.nodes)
    assert nodal_results[utils.TEST_NODE_UUID] == grid.nodal_result(
        utils.TEST_NODE_UUID
    )


def test_nodal_energies():
    nodal_energies = grid.nodal_energies()
    assert nodal_energies[utils.TEST_NODE_UUID] == grid.nodal_energy(
        utils.TEST_NODE_UUID
    )


def test_build_enhanced_nodes_result():
    enhanced_node_results = grid.build_enhanced_nodes_result()
    assert len(enhanced_node_results) == 299
    node_res = grid.nodal_result(utils.TEST_NODE_UUID)
    p = node_res.participants.p_sum().rename("p")
    q = node_res.participants.q_sum().rename("q")
    expected = EnhancedNodeResult.from_node_result(
        node_res.nodes.nodes[utils.TEST_NODE_UUID], p, q
    )
    assert enhanced_node_results.nodes[utils.TEST_NODE_UUID] == expected
