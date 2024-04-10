import math

import numpy as np
import pandas as pd

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.grid.transformer import Transformer2WResult
from tests.models.result.grid.test_node import get_node_result


def get_connector_result(i_a_angs, i_a_mags, i_b_angs, i_b_mags):
    data = pd.DataFrame(
        {
            "i_a_ang": i_a_angs,
            "i_a_mag": i_a_mags,
            "i_b_ang": i_b_angs,
            "i_b_mag": i_b_mags,
        }
    )
    return Transformer2WResult(
        RawGridElementsEnum.TRANSFORMER_2_W,
        "uuid",
        None,
        data,
    )


def test_lines_result(gwr):
    lines_res = gwr.results.lines
    lines_uuids = set(lines_res.uuids())
    expected_nr_uuids = len(gwr.grid.raw_grid.lines)
    check_connector_res(lines_res, lines_uuids, expected_nr_uuids)


def check_connector_res(connector_res, connectors_uuids, expected_nr_uuids):
    assert len(connector_res) == expected_nr_uuids
    assert len(connector_res.i_a_ang().columns) == expected_nr_uuids
    assert set(connector_res.i_a_ang().columns) == connectors_uuids
    assert len(connector_res.i_a_mag().columns) == expected_nr_uuids
    assert set(connector_res.i_a_mag().columns) == connectors_uuids
    assert len(connector_res.i_b_ang().columns) == expected_nr_uuids
    assert set(connector_res.i_b_ang().columns) == connectors_uuids
    assert len(connector_res.i_b_mag().columns) == expected_nr_uuids
    assert set(connector_res.i_b_mag().columns) == connectors_uuids


def test_line_result(gwr):
    t_res = gwr.results.lines.results()[0]
    assert set(t_res.data.columns) == set(t_res.attributes())


def test_calc_apparent_power():
    i_a_mags = [1, 2, 3]
    i_a_angs = [4, 5, 6]
    i_b_mags = [2, 3, 4]
    i_b_angs = [5, 6, 7]
    v_angs = [1, 1, 1]
    v_mags = [1.01, 1.02, 1.03]

    trafo = get_connector_result(
        i_a_angs=i_a_angs, i_a_mags=i_a_mags, i_b_angs=i_b_angs, i_b_mags=i_b_mags
    )
    node_res = get_node_result(v_mags=v_mags, v_angs=v_angs)

    def apparent_power(v_mag, v_ang, i_mag, i_ang):
        u_complex = v_mag * np.exp(1j * np.radians(v_ang))
        i_complex = i_mag * np.exp(1j * np.radians(i_ang))
        return math.sqrt(3) * u_complex * np.conj(i_complex)

    apparent_power_a = trafo.calc_apparent_power(node_res, voltage_level_kv=1, node="a")
    expected_a = [
        apparent_power(v_mags[i], v_angs[i], i_a_mags[i], i_a_angs[i])
        for i in range(len(v_mags))
    ]
    assert np.allclose(apparent_power_a, expected_a)

    apparent_power_b = trafo.calc_apparent_power(node_res, voltage_level_kv=1, node="b")
    expected_b = [
        apparent_power(v_mags[i], v_angs[i], i_b_mags[i], i_b_angs[i])
        for i in range(len(v_mags))
    ]
    assert np.allclose(apparent_power_b, expected_b)
