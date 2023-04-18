from datetime import datetime


def test_filter_for_time_interval(gwr):
    nodes_res = gwr.results.nodes
    start = datetime(year=2011, month=1, day=1, hour=13)
    end = datetime(year=2011, month=1, day=1, hour=13)
    node_uuid = "401f37f8-6f2c-4564-bc78-6736cb9cbf8d"
    test_node_res = nodes_res.entities[node_uuid]
    filtered_test_node_res = test_node_res.filter_for_time_interval(start, end)
    assert len(filtered_test_node_res) == 1
    filtered = nodes_res.filter_for_time_interval(start, end)
    assert filtered.entities[node_uuid] == filtered_test_node_res


def test_vmags(gwr):
    nodes_res = gwr.results.nodes
    v_mags = nodes_res.v_mag
    assert len(v_mags) == 3
    assert len(v_mags.columns) == 299


def test_vangs(gwr):
    nodes_res = gwr.results.nodes
    v_angs = nodes_res.v_ang
    assert len(v_angs) == 3
    assert len(v_angs.columns) == 299
