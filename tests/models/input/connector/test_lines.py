import pandas as pd
import pytest

from psdm_analysis.models.input.connector.lines import Lines


@pytest.fixture
def lines_fixture():
    df = pd.DataFrame(
        {
            "length": [10, 20, 30],
            "geo_position": [(12, 13), (22, 23), (32, 33)],
            "olm_characteristic": ["c1", "c2", "c3"],
            "v_rated": [100, 200, 300],
            "r": [1, 2, 3],
            "x": [4, 5, 6],
            "b": [7, 8, 9],
            "i_max": [10, 20, 30],
            "node_a": ["uuid1", "uuid2", "uuid3"],
            "node_b": ["uuid4", "uuid5", "uuid6"],
        }
    )
    return Lines(df)


def test_properties(lines_fixture):
    assert (lines_fixture.length == pd.Series([10, 20, 30])).all()
    assert (
        lines_fixture.geo_position == pd.Series([(12, 13), (22, 23), (32, 33)])
    ).all()
    assert (lines_fixture.olm_characteristic == pd.Series(["c1", "c2", "c3"])).all()
    assert (lines_fixture.v_rated == pd.Series([100, 200, 300])).all()
    assert (lines_fixture.r == pd.Series([1, 2, 3])).all()
    assert (lines_fixture.x == pd.Series([4, 5, 6])).all()
    assert (lines_fixture.b == pd.Series([7, 8, 9])).all()
    assert (lines_fixture.i_max == pd.Series([10, 20, 30])).all()


def test_aggregated_line_length(lines_fixture):
    assert lines_fixture.aggregated_line_length() == 60


def test_relative_line_length(lines_fixture):
    assert (
        lines_fixture.relative_line_length() == pd.Series([10 / 3, 20 / 3, 30 / 3])
    ).all()


def test_find_lines_by_nodes(lines_fixture):
    found_lines = lines_fixture.filter_by_nodes(["uuid1", "uuid3"])
    assert (found_lines.data == lines_fixture.data.loc[[0, 2], :]).all().all()


def test_find_line_by_node_pair(lines_fixture):
    found_line = lines_fixture.filter_by_node_pair("uuid2", "uuid5")
    assert (found_line.data == lines_fixture.data.loc[[1], :]).all().all()
