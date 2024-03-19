from io import StringIO

import pandas as pd

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.grid.extended_node import ExtendedNodeResult


def test_data_pf():
    data_str = """
    time,v_mag,v_ang,p,q
    2020-01-01 00:00:00,1.0,0.0,1.0,0.0
    2020-01-01 00:30:00,NaN,NaN,2.0,1.0
    2020-01-01 01:00:00,2.0,1.0,3.0,2.0
    2020-01-01 01:15:00,NaN,NaN,3.5,2.5
    2020-01-01 01:30:00,NaN,NaN,4.0,3.0
    2020-01-01 02:00:00,3.0,2.0,5.0,4.0
    """

    data_io = StringIO(data_str)
    data = pd.read_csv(data_io, sep=",", index_col=0, parse_dates=True)

    expected_str = """
    time,v_mag,v_ang,p,q
    2020-01-01 00:00:00,1.0,0.0,0.000,0.000
    2020-01-01 01:00:00,2.0,1.0,1.500,0.500
    2020-01-01 02:00:00,3.0,2.0,3.625,2.625
    """
    expected_data = pd.read_csv(
        StringIO(expected_str), sep=",", index_col=0, parse_dates=True
    )

    nodes_res = ExtendedNodeResult(RawGridElementsEnum.NODE, "node_1", "node_1", data)

    actual_data = nodes_res.data_pf()
    pd.testing.assert_frame_equal(actual_data, expected_data)

    pd.testing.assert_series_equal(nodes_res.p_pf(), expected_data["p"])
    pd.testing.assert_series_equal(nodes_res.q_pf(), expected_data["q"])


def test_data_pf_vec():
    data_str = """
    time,v_mag,v_ang,p,q
    2020-01-01 00:00:00,1.0,0.0,1.0,0.0
    2020-01-01 00:30:00,NaN,NaN,2.0,1.0
    2020-01-01 01:00:00,2.0,1.0,3.0,2.0
    2020-01-01 01:15:00,NaN,NaN,3.5,2.5
    2020-01-01 01:30:00,NaN,NaN,4.0,3.0
    2020-01-01 02:00:00,3.0,2.0,5.0,4.0
    """

    data_io = StringIO(data_str)
    data = pd.read_csv(data_io, sep=",", index_col=0, parse_dates=True)

    expected_str = """
    time,v_mag,v_ang,p,q
    2020-01-01 00:00:00,1.0,0.0,0.000,0.000
    2020-01-01 01:00:00,2.0,1.0,1.500,0.500
    2020-01-01 02:00:00,3.0,2.0,3.625,2.625
    """
    expected_data = pd.read_csv(
        StringIO(expected_str), sep=",", index_col=0, parse_dates=True
    )

    nodes_res = ExtendedNodeResult(RawGridElementsEnum.NODE, "node_1", "node_1", data)

    actual_data = nodes_res.data_pf()
    pd.testing.assert_frame_equal(actual_data, expected_data)
    pd.testing.assert_series_equal(nodes_res.p_pf(), expected_data["p"])
    pd.testing.assert_series_equal(nodes_res.q_pf(), expected_data["q"])
    actual_data = nodes_res.data_pf()
    assert hasattr(
        nodes_res, "_ExtendedNodeResult__data_pf"
    ), "Expected cached attribute"
