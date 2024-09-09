from pypsdm.models.input import Nodes, Lines
from pypsdm.models.input.create.utils import create_data
from uuid import uuid4
import pandas as pd


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
    type,
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
            "type": type,
            "olm_characteristic": olm_characteristic,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "parallel_devices": parallel_devices,
        }
    ).rename(uuid)
