from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Union

from psdm_analysis.models.input.container.mixins import ContainerMixin
from psdm_analysis.models.input.container.participants import (
    SystemParticipantsContainer,
)
from psdm_analysis.models.input.container.raw_grid import RawGridContainer
from psdm_analysis.models.primary_data import PrimaryData
from psdm_analysis.models.result.power import PQResult


@dataclass(frozen=True)
class GridContainer(ContainerMixin):
    raw_grid: RawGridContainer
    # TODO: we keep the participant containers effectively twice with the mapping
    participants: SystemParticipantsContainer
    primary_data: PrimaryData
    node_participants_map: Dict[str, SystemParticipantsContainer]

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

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return GridContainer(
            raw_grid=self.raw_grid,
            participants=self.participants,
            primary_data=self.primary_data.filter_by_date_time(time),
            node_participants_map=self.node_participants_map,
        )

    def to_csv(
        self,
        path: str,
        include_primary_data: bool,
        mkdirs: bool = True,
        delimiter: str = ",",
    ):
        for container in self.to_list(include_primary_data=include_primary_data):
            try:
                container.to_csv(path, mkdirs=mkdirs, delimiter=delimiter)
            except Exception as e:
                raise IOError(f"Could not write {container} to {path}.", e)

    @classmethod
    def from_csv(cls, path: str, delimiter: str, primary_data_delimiter: str = None):
        if not primary_data_delimiter:
            primary_data_delimiter = delimiter
        raw_grid = RawGridContainer.from_csv(path, delimiter)
        participants = SystemParticipantsContainer.from_csv(path, delimiter)
        node_participants_map = participants.build_node_participants_map(raw_grid.nodes)
        primary_data = PrimaryData.from_csv(path, primary_data_delimiter)
        return cls(raw_grid, participants, primary_data, node_participants_map)
