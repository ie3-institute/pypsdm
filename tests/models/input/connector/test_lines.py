import math
import os

import numpy as np
import pandas as pd
import pytest

from pypsdm import Lines
from pypsdm.models.input.container.grid import GridContainer
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


def test_to_csv(lines: Lines, tmp_path):
    path = os.path.join(tmp_path, "lines")
    os.makedirs(path, exist_ok=True)
    lines.to_csv(path)
    lines2 = Lines.from_csv(path)
    # todo this needs to be tested for other participants
    compare_dfs(lines.data, lines2.data)


def test_gij(simple_grid: GridContainer):
    gij = simple_grid.lines.gij()

    uuid = "ca425259-fab4-4dc1-99c9-c19031121645"
    line = simple_grid.lines[uuid]
    length = line.length
    r = line.r * length
    x = line.x * length
    l_gij = r / (r**2 + x**2)

    assert math.isclose(gij[uuid], l_gij)

    # SIMONA pu result
    nom_imp = 0.266666666666666
    assert math.isclose(gij[uuid], 26.066167336648626 / nom_imp)


def test_bij(simple_grid: GridContainer):
    bij = simple_grid.lines.bij()

    uuid = "ca425259-fab4-4dc1-99c9-c19031121645"

    # SIMONA pu result
    nom_imp = 0.266666666666666
    assert math.isclose(bij[uuid], -6.679455380016211 / nom_imp)


def test_yij(simple_grid: GridContainer):
    yij = simple_grid.lines.yij()

    uuid = "ca425259-fab4-4dc1-99c9-c19031121645"

    # SIMONA pu result
    nom_imp = 0.266666666666666
    expected = (26.066167336648626 + 1j * -6.679455380016211,)
    assert math.isclose(yij[uuid].real, expected[0].real / nom_imp)
    assert math.isclose(yij[uuid].imag, expected[0].imag / nom_imp)


def test_yi0(simple_grid: GridContainer):
    y0 = simple_grid.lines.y0()
    uuid = "ca425259-fab4-4dc1-99c9-c19031121645"

    # SIMONA pu result
    nom_imp = 0.266666666666666
    expected = 0.0 + 1j * 6.534520000000001 * 1e-7
    assert math.isclose(y0[uuid].real, expected.real / nom_imp)
    assert math.isclose(y0[uuid].imag, expected.imag / nom_imp)


def test_admittance_matrix(simple_grid):
    uuid_idx = {
        "b7a5be0d-2662-41b2-99c6-3b8121a75e9e": 0,
        "df97c0d1-379b-417a-a473-8e7fe37da99d": 1,
        "1dcddd06-f41a-405b-9686-7f7942852196": 2,
        "e3c3c6a3-c383-4dbb-9b3f-a14125615386": 3,
        "6a4547a8-630b-46e4-8144-9cd649e67c07": 4,
    }

    Y = simple_grid.lines.admittance_matrix(uuid_idx)

    # SIMONA pu result
    nom_imp = 0.266666666666666
    first_row = [
        32.081436722029075 + 1j * -8.220864674942618,
        0,
        -6.015269385380451 + 1j * 1.5414127800037403,
        0,
        -26.066167336648626 + 1j * 6.679455380016211,
    ]
    expected = [x / nom_imp for x in first_row]

    assert np.allclose(Y[0], expected)
