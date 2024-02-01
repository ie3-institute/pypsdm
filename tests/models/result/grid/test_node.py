from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.grid.node import NodeResult, NodesResult


def get_node_result(v_mags, v_angs):
    data = pd.DataFrame(
        {
            "v_mag": v_mags,
            "v_ang": v_angs,
        }
    )
    return NodeResult(RawGridElementsEnum.NODE, "test_node", None, data)


def test_compare():
    a = get_node_result(v_mags=[1, 2, 3], v_angs=[1, 2, 3])
    b = get_node_result(v_mags=[1, 2, 3], v_angs=[1, 2, 3])
    assert a == b


def test_v_complex_pos_angle():
    v_mags = [1.01, 1.02, 1.03]
    v_angs = [1, 2, 3]
    node = get_node_result(v_mags=v_mags, v_angs=v_angs)
    v_rated = 10
    v_complex = node.v_complex(v_rated)
    assert len(v_complex) == 3
    assert list(np.abs(v_complex) / 10) == pytest.approx(v_mags)
    assert list(np.degrees(np.angle(v_complex))) == pytest.approx(v_angs)


def test_v_complex_neg_angle():
    v_mags = [1.01, 1.02, 1.03]
    v_angs = [-1, -2, -3]
    node = get_node_result(v_mags=v_mags, v_angs=v_angs)
    v_rated = 10
    v_complex = node.v_complex(v_rated)
    assert len(v_complex) == 3
    assert list(np.abs(v_complex) / 10) == pytest.approx(v_mags)
    assert list(np.degrees(np.angle(v_complex))) == pytest.approx(v_angs)


def test_filter_for_time_interval(gwr):
    nodes_res = gwr.results.nodes
    start = datetime(year=2011, month=1, day=1, hour=13)
    end = datetime(year=2011, month=1, day=1, hour=13)
    node_uuid = "401f37f8-6f2c-4564-bc78-6736cb9cbf8d"
    test_node_res = nodes_res.entities[node_uuid]
    filtered_test_node_res = test_node_res.filter_for_time_interval(start, end)
    assert len(filtered_test_node_res) == 1
    filtered = nodes_res.filter_for_time_interval(start, end)
    entity = filtered.entities[node_uuid]
    assert entity == filtered_test_node_res


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


def test_create_empty():
    empty = NodesResult.create_empty()
    if empty:
        raise AssertionError("Empty NodesResult should be falsy")
