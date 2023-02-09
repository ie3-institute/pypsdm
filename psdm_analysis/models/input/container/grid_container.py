from dataclasses import dataclass
from typing import Dict

from psdm_analysis.models.entity import Entities
from psdm_analysis.models.input.connector.lines import Lines
from psdm_analysis.models.input.connector.transformer import Transformers2W
from psdm_analysis.models.input.container.participants_container import (
    SystemParticipantsContainer,
)
from psdm_analysis.models.input.node import Nodes
from psdm_analysis.models.primary_data import PrimaryData
from psdm_analysis.models.result.power import PQResult


@dataclass(frozen=True)
class RawGridContainer:
    nodes: Nodes
    lines: Lines
    transformers_2_w: Transformers2W

    def to_list(self, include_empty: bool = False) -> list[Entities]:
        grid_elements = [self.nodes, self.lines, self.transformers_2_w]
        return grid_elements if include_empty else [e for e in grid_elements if e]

    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "RawGridContainer":
        nodes = Nodes.from_csv(path, delimiter)
        lines = Lines.from_csv(path, delimiter)
        transformers_2_w = Transformers2W.from_csv(path, delimiter)
        return cls(nodes=nodes, lines=lines, transformers_2_w=transformers_2_w)


@dataclass(frozen=True)
class GridContainer:
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
            uuid: participants.filter_by_node(uuid) for uuid in raw_grid.nodes.uuids()
        }
        primary_data = PrimaryData.from_csv(path, primary_data_delimiter)
        return cls(raw_grid, participants, primary_data, node_participants_map)

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
