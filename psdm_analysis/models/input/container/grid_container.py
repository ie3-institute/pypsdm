from dataclasses import dataclass
from typing import Dict

from psdm_analysis.models.entity import Entities
from psdm_analysis.models.input.connector.lines import Lines
from psdm_analysis.models.input.connector.switches import Switches
from psdm_analysis.models.input.connector.transformer import Transformers2W
from psdm_analysis.models.input.container.mixins import ContainerMixin
from psdm_analysis.models.input.container.participants_container import (
    SystemParticipantsContainer,
)
from psdm_analysis.models.input.node import Nodes
from psdm_analysis.models.primary_data import PrimaryData
from psdm_analysis.models.result.power import PQResult


@dataclass(frozen=True)
class RawGridContainer(ContainerMixin):
    nodes: Nodes
    lines: Lines
    transformers_2_w: Transformers2W
    switches: Switches

    def to_list(self, include_empty: bool = False) -> list[Entities]:
        grid_elements = [self.nodes, self.lines, self.transformers_2_w, self.switches]
        return grid_elements if include_empty else [e for e in grid_elements if e]

    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "RawGridContainer":
        nodes = Nodes.from_csv(path, delimiter)
        lines = Lines.from_csv(path, delimiter)
        transformers_2_w = Transformers2W.from_csv(path, delimiter)
        switches = Switches.from_csv(path, delimiter)
        return cls(
            nodes=nodes,
            lines=lines,
            transformers_2_w=transformers_2_w,
            switches=switches,
        )


@dataclass(frozen=True)
class GridContainer(ContainerMixin):
    raw_grid: RawGridContainer
    # todo: we keep the participant containers effectively twice with the mapping
    participants: SystemParticipantsContainer
    primary_data: PrimaryData
    node_participants_map: Dict[str, SystemParticipantsContainer]

    @classmethod
    def from_csv(cls, path: str, delimiter: str, primary_data_delimiter: str = None):
        if not primary_data_delimiter:
            primary_data_delimiter = delimiter
        raw_grid = RawGridContainer.from_csv(path, delimiter)
        participants = SystemParticipantsContainer.from_csv(path, delimiter)
        node_participants_map = {
            uuid: participants.filter_by_node(uuid) for uuid in raw_grid.nodes.uuids
        }
        primary_data = PrimaryData.from_csv(path, primary_data_delimiter)
        return cls(raw_grid, participants, primary_data, node_participants_map)

    def to_list(self, include_empty: bool = False, include_primary_data: bool = False):
        grid = [self.raw_grid, self.participants]
        return grid if not include_primary_data else grid + [self.primary_data]

    def get_nodal_primary_data(self):
        time_series = []
        nodal_primary_data = dict()
        for node, participants_container in self.node_participants_map.items():
            participants_uuids = participants_container.uuids().tolist()
            node_primary_data = self.primary_data.get_for_participants(
                participants_uuids
            )
            time_series.extend(node_primary_data)
            node_primary_data_agg = PQResult.sum(node_primary_data)
            nodal_primary_data[node] = node_primary_data_agg
        return nodal_primary_data

    def get_nodal_sp_count_and_power(self):
        data = {}
        for node_uuid, sps in self.node_participants_map.items():
            nodal_data = {}
            for sp in sps.to_list(include_empty=False):
                sp_id = sp.get_enum().value
                count = len(sp.data)
                data_str = f"Count: {count}"
                # check if sp has a property named s_rated
                if hasattr(sp, "s_rated"):
                    s_rated = round(sp.s_rated.sum(), 2)
                    data_str += f", Rated Power: {s_rated} kw"
                nodal_data[sp_id] = data_str
            data[node_uuid] = nodal_data
        return data
