from datetime import datetime, timedelta

import pandas as pd

from pypsdm.models.enums import (
    EntitiesEnum,
    RawGridElementsEnum,
    SystemParticipantsEnum,
)
from pypsdm.models.result.grid.node import NodeResult, NodesResult
from pypsdm.models.result.participant.pq_dict import PQResultDict
from pypsdm.models.result.power import PQResult

# These are just some early quite specific conversions. Additional ones will be added as needed.


def pp_load_to_participants_result(
    pp_net_file: str,  # pp net xlsx export
    participant_p_file: str,  # pp time series p_mw export
    participant_q_file: str,  # pp time series q_mvar export
    psdm_load_file: str,  # psdm load csv input
    start: datetime,  # start of the time series simulation
    resolution: timedelta,  # resolution of the time series simulation
) -> PQResultDict:
    return _pp_to_psdm_result(
        entity_type=SystemParticipantsEnum.LOAD,
        pp_net_file=pp_net_file,
        pp_sheet_name="load",
        pp_attribute_a_file=participant_p_file,
        psdm_attribute_a_name="p",
        pp_attribute_b_file=participant_q_file,
        psdm_attribute_b_name="q",
        psdm_entity_input_file=psdm_load_file,
        start=start,
        resolution=resolution,
        res_entity_class=PQResult,
        res_dict_class=PQResultDict,
    )


def pp_node_to_nodes_result(
    pp_net_file: str,  # pp net xlsx export
    node_vm_file: str,  # pp time series vm_pu export
    node_va_file: str,  # pp time series va_degree export
    psdm_node_file: str,  # psdm node csv input
    start: datetime,  # start of the time series simulation
    resolution: timedelta,  # resolution of the time series simulation
) -> PQResultDict:
    return _pp_to_psdm_result(
        entity_type=RawGridElementsEnum.NODE,
        pp_net_file=pp_net_file,
        pp_sheet_name="bus",
        pp_attribute_a_file=node_vm_file,
        psdm_attribute_a_name="v_mag",
        pp_attribute_b_file=node_va_file,
        psdm_attribute_b_name="v_ang",
        psdm_entity_input_file=psdm_node_file,
        start=start,
        resolution=resolution,
        res_entity_class=NodeResult,
        res_dict_class=NodesResult,
    )


def _pp_to_psdm_result(
    entity_type: EntitiesEnum,
    pp_net_file: str,
    pp_sheet_name: str,
    pp_attribute_a_file: str,
    psdm_attribute_a_name: str,
    pp_attribute_b_file: str,
    psdm_attribute_b_name: str,
    psdm_entity_input_file: str,
    start: datetime,
    resolution: timedelta,
    res_entity_class,
    res_dict_class,
):
    pp_entity = pd.read_excel(pp_net_file, sheet_name=pp_sheet_name, index_col=0)
    idx_to_id = pp_entity["name"].to_dict()
    psdm_entity = pd.read_csv(psdm_entity_input_file, sep=";", index_col=0)
    id_to_uuid = {id: uuid for uuid, id in psdm_entity["id"].to_dict().items()}
    idx_to_uuid = {idx: id_to_uuid[id] for idx, id in idx_to_id.items()}
    pp_attribute_a = pd.read_json(pp_attribute_a_file)
    pp_attribute_b = pd.read_json(pp_attribute_b_file)
    pp_attribute_a["time"] = pd.date_range(
        start=start, periods=len(pp_attribute_a), freq=resolution
    )
    pp_attribute_a.set_index("time", inplace=True)
    pp_attribute_b["time"] = pd.date_range(
        start=start, periods=len(pp_attribute_a), freq=resolution
    )
    pp_attribute_b.set_index("time", inplace=True)
    participants = {}

    for ts in pp_attribute_a.columns:
        data = pd.concat(
            [
                pp_attribute_a[ts].rename(psdm_attribute_a_name),
                pp_attribute_b[ts].rename(psdm_attribute_b_name),
            ],
            axis=1,
        )
        uuid = idx_to_uuid[ts]
        node_res = res_entity_class(
            type=entity_type, name=idx_to_id[ts], input_model=uuid, data=data
        )
        participants[uuid] = node_res

    return res_dict_class(entity_type=entity_type, entities=participants)
