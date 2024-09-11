from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Union

from pypsdm.models.enums import (
    EntitiesEnum,
    RawGridElementsEnum,
    SystemParticipantsEnum,
)
from pypsdm.models.input.container.mixins import ContainerMixin
from pypsdm.models.input.container.participants import SystemParticipantsContainer
from pypsdm.models.input.container.raw_grid import RawGridContainer
from pypsdm.models.ts.types import ComplexPower
from pypsdm.plots.common.utils import RGB
from pypsdm.plots.grid import grid_plot

if TYPE_CHECKING:
    from pypsdm.models.primary_data import PrimaryData


@dataclass(frozen=True)
class GridContainer(ContainerMixin):
    raw_grid: RawGridContainer
    # TODO: we keep the participant containers effectively twice with the mapping
    participants: SystemParticipantsContainer
    primary_data: PrimaryData
    node_participants_map: Dict[str, SystemParticipantsContainer]

    def __eq__(self, other):
        if not isinstance(other, GridContainer):
            return False
        if not self.node_participants_map == other.node_participants_map:
            return False
        return super().__eq__(other)

    def __bool__(self):
        return len(self.to_list(include_primary_data=True)) > 0

    @property
    def nodes(self):
        return self.raw_grid.nodes

    @property
    def lines(self):
        return self.raw_grid.lines

    @property
    def transformers_2_w(self):
        return self.raw_grid.transformers_2_w

    @property
    def switches(self):
        return self.raw_grid.switches

    @property
    def ems(self):
        return self.participants.ems

    @property
    def loads(self):
        return self.participants.loads

    @property
    def fixed_feed_ins(self):
        return self.participants.fixed_feed_ins

    @property
    def pvs(self):
        return self.participants.pvs

    @property
    def biomass_plants(self):
        return self.participants.biomass_plants

    @property
    def wecs(self):
        return self.participants.wecs

    @property
    def storages(self):
        return self.participants.storages

    @property
    def evs(self):
        return self.participants.evs

    @property
    def evcs(self):
        return self.participants.evcs

    @property
    def hps(self):
        return self.participants.hps

    def to_list(self, include_empty: bool = False, include_primary_data: bool = False):
        grid = (
            [self.raw_grid, self.participants, self.primary_data]
            if include_primary_data
            else [self.raw_grid, self.participants]
        )
        return grid if include_empty else [g for g in grid if g]

    def get_nodal_primary_data(self):
        time_series = []
        nodal_primary_data = dict()
        for node, participants_container in self.node_participants_map.items():
            participants_uuids = participants_container.uuids().tolist()
            node_primary_data = self.primary_data.get_for_participants(
                participants_uuids
            )
            time_series.extend(node_primary_data)
            node_primary_data_agg = ComplexPower.sum(node_primary_data)
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

    def get_with_enum(self, enum: EntitiesEnum):
        if isinstance(enum, RawGridElementsEnum):
            return self.raw_grid.get_with_enum(enum)
        if isinstance(enum, SystemParticipantsEnum):
            return self.participants.get_with_enum(enum)
        raise ValueError(f"Unretrievable enum {enum}")

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return GridContainer(
            raw_grid=self.raw_grid,
            participants=self.participants,
            primary_data=self.primary_data.filter_by_date_time(time),
            node_participants_map=self.node_participants_map,
        )

    def filter_by_nodes(self, nodes: str | list[str]):
        raw_grid = self.raw_grid.filter_by_nodes(nodes)
        participants = self.participants.filter_by_nodes(nodes)
        primary_data = self.primary_data.filter_by_participants(
            participants.uuids().tolist(),
            skip_missing=True,
        )
        node_participants_map = participants.build_node_participants_map(raw_grid.nodes)
        return GridContainer(
            raw_grid=raw_grid,
            participants=participants,
            primary_data=primary_data,
            node_participants_map=node_participants_map,
        )

    def plot_grid(
        self,
        node_highlights: Optional[Union[dict[RGB, list[str]], list[str]]] = None,
        line_highlights: Optional[Union[dict[RGB, list[str]], list[str]]] = None,
        highlight_disconnected: Optional[bool] = False,
    ):
        return grid_plot(self, node_highlights, line_highlights, highlight_disconnected)

    def to_csv(
        self,
        path: str | Path,
        include_primary_data: bool = True,
        mkdirs: bool = False,
        delimiter: str = ",",
    ):
        for container in self.to_list(include_primary_data=include_primary_data):
            try:
                container.to_csv(path, mkdirs=mkdirs, delimiter=delimiter)
            except Exception as e:
                raise IOError(f"Could not write {container} to {path}.", e)

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        delimiter: str | None = None,
        primary_data_delimiter: Optional[str] = None,
    ):
        from pypsdm.models.primary_data import PrimaryData

        if not primary_data_delimiter:
            primary_data_delimiter = delimiter
        raw_grid = RawGridContainer.from_csv(path, delimiter)
        participants = SystemParticipantsContainer.from_csv(path, delimiter)
        node_participants_map = participants.build_node_participants_map(raw_grid.nodes)
        primary_data = PrimaryData.from_csv(path, primary_data_delimiter)
        return cls(raw_grid, participants, primary_data, node_participants_map)

    @classmethod
    def empty(cls):
        from pypsdm.models.primary_data import PrimaryData

        return cls(
            raw_grid=RawGridContainer.empty(),
            participants=SystemParticipantsContainer.empty(),
            primary_data=PrimaryData.create_empty(),
            node_participants_map=dict(),
        )
