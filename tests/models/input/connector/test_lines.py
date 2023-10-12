import os

import pandas as pd
import pytest

from pypsdm.models.input.connector.lines import Lines
from pypsdm.processing.dataframe import compare_dfs


@pytest.fixture
def lines():
    df = pd.DataFrame(
        {
            "id": ["id1", "id2", "id3"],
            "operator": ["op1", "op2", "op3"],
            "operates_from": ["2020-01-04", "2020-01-05", "2020-01-06"],
            "operates_until": ["2020-01-01", "2020-01-02", "2020-01-03"],
            "parallel_devices": [1, 2, 3],
            "length": [10, 20, 30],
            "geo_position": ["(12, 13)", "(22, 23)", "(32, 33)"],
            "olm_characteristic": ["c1", "c2", "c3"],
            "v_rated": [100, 200, 300],
            "r": [1, 2, 3],
            "x": [4, 5, 6],
            "b": [7, 8, 9],
            "g": [10, 11, 12],
            "i_max": [10, 20, 30],
            "node_a": ["uuid1", "uuid2", "uuid3"],
            "node_b": ["uuid4", "uuid5", "uuid6"],
            "type_uuid": ["uuidtype1", "uuidtype2", "uuidtype3"],
            "type_id": ["idtype1", "idtype2", "idtype3"],
        }
    )
    return Lines(df.rename_axis("uuid"))


def test_properties(lines):
    assert (lines.length == pd.Series([10, 20, 30])).all()
    assert (lines.geo_position == pd.Series(["(12, 13)", "(22, 23)", "(32, 33)"])).all()
    assert (lines.olm_characteristic == pd.Series(["c1", "c2", "c3"])).all()
    assert (lines.v_rated == pd.Series([100, 200, 300])).all()
    assert (lines.r == pd.Series([1, 2, 3])).all()
    assert (lines.x == pd.Series([4, 5, 6])).all()
    assert (lines.b == pd.Series([7, 8, 9])).all()
    assert (lines.i_max == pd.Series([10, 20, 30])).all()


def test_aggregated_line_length(lines):
    assert lines.aggregated_line_length() == 60


def test_relative_line_length(lines):
    assert (lines.relative_line_length() == pd.Series([10 / 3, 20 / 3, 30 / 3])).all()


def test_find_lines_by_nodes(lines):
    found_lines = lines.filter_by_nodes(["uuid1", "uuid3"])
    assert (found_lines.data == lines.data.loc[[0, 2], :]).all().all()


def test_find_line_by_node_pair(lines):
    found_line = lines.filter_by_node_pair("uuid2", "uuid5")
    assert (found_line.data == lines.data.loc[[1], :]).all().all()


def test_attributes(lines):
    assert set(lines.attributes()) == set(lines.data.columns)


def test_to_csv(lines: Lines, tmp_path, delimiter):
    path = os.path.join(tmp_path, "lines")
    os.makedirs(path, exist_ok=True)
    lines.to_csv(path, delimiter)
    lines2 = Lines.from_csv(path, delimiter)
    # todo this needs to be tested for other participants
    compare_dfs(lines.data, lines2.data)
