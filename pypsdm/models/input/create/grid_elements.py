from uuid import uuid4

import pandas as pd

from pypsdm.models.input import Lines, Nodes, Transformers2W
from pypsdm.models.input.create.utils import create_data


def create_nodes(data_dict):
    return Nodes(create_data(data_dict, create_nodes_data))


def create_nodes_data(
    geo_position,
    id,
    subnet,
    v_rated,
    v_target,
    volt_lvl,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
    slack=False,
):
    if not uuid:
        uuid = str(uuid4())
    return pd.Series(
        {
            "geo_position": geo_position,
            "id": id,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "slack": slack,
            "subnet": subnet,
            "v_rated": v_rated,
            "v_target": v_target,
            "volt_lvl": volt_lvl,
        }
    ).rename(uuid)


def create_lines(data_dict):
    return Lines(create_data(data_dict, create_lines_data))


def create_lines_data(
    geo_position,
    id,
    length,
    node_a,
    node_b,
    b,
    g,
    i_max,
    r,
    v_rated,
    x,
    olm_characteristic="olm:{(0.0,1.0)}",
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
    parallel_devices=1,
):
    if not uuid:
        uuid = str(uuid4())
    return pd.Series(
        {
            "geo_position": geo_position,
            "id": id,
            "length": length,
            "node_a": node_a,
            "node_b": node_b,
            "b": b,
            "g": g,
            "i_max": i_max,
            "r": r,
            "v_rated": v_rated,
            "x": x,
            "olm_characteristic": olm_characteristic,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "parallel_devices": parallel_devices,
        }
    ).rename(uuid)


def create_2w_transformers(data_dict):
    return Transformers2W(create_data(data_dict, create_2w_transformer_data))


def create_2w_transformer_data(
    auto_tap,
    id,
    node_a,
    node_b,
    tap_pos,
    tap_max,
    tap_min,
    tap_neutr,
    tap_side,
    v_rated_a,
    v_rated_b,
    d_phi,
    d_v,
    r_sc,
    x_sc,
    g_m,
    b_m,
    s_rated,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
    parallel_devices=1,
):
    if not uuid:
        uuid = str(uuid4())
    return pd.Series(
        {
            "auto_tap": auto_tap,
            "id": id,
            "node_a": node_a,
            "node_b": node_b,
            "tap_pos": tap_pos,
            'tap_max': tap_max,
            'tap_min': tap_min,
            'tap_neutr': tap_neutr,
            'tap_side': tap_side,
            'v_rated_a': v_rated_a,
            'v_rated_b': v_rated_b,
            'd_phi': d_phi,
            'd_v': d_v,
            'r_sc': r_sc,
            'x_sc': x_sc,
            'g_m': g_m,
            'b_m': b_m,
            's_rated': s_rated,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "parallel_devices": parallel_devices,
        }
    ).rename(uuid)
