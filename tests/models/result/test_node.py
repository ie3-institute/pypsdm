from datetime import datetime

from psdm_analysis.models.result.grid.node import NodesResult
from tests import utils

simulation_end = datetime(year=2011, month=1, day=1, hour=14)
nodes_res = NodesResult.from_csv(
    utils.VN_SIMONA_RESULT_PATH, utils.VN_SIMONA_DELIMITER, simulation_end
)
assert len(nodes_res) == 299


def test_filter_for_time_interval():
    start = datetime(year=2011, month=1, day=1, hour=13)
    end = datetime(year=2011, month=1, day=1, hour=13)
    test_node_res = nodes_res.entities[utils.TEST_NODE_UUID]
    filtered_test_node_res = test_node_res.filter_for_time_interval(start, end)
    assert len(filtered_test_node_res) == 1
    filtered = nodes_res.filter_for_time_interval(start, end)
    assert filtered.entities[utils.TEST_NODE_UUID] == filtered_test_node_res


def test_vmags():
    v_mags = nodes_res.v_mags()
    assert len(v_mags) == 2
    assert len(v_mags.columns) == 299


def test_vangs():
    v_angs = nodes_res.v_angs()
    assert len(v_angs) == 2
    assert len(v_angs.columns) == 299
