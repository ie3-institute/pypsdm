from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
import pandas as pd
from loguru import logger

from pypsdm.io.utils import check_filter
from pypsdm.models.input.container.grid import GridContainer
from pypsdm.models.input.container.mixins import ContainerMixin
from pypsdm.models.input.container.participants import SystemParticipantsContainer
from pypsdm.models.result.container.grid import GridResultContainer
from pypsdm.models.result.container.participants import (
    SystemParticipantsResultContainer,
)
from pypsdm.models.ts.types import ComplexVoltagePower, ComplexVoltagePowerDict
from pypsdm.plots.common.utils import RGB


@dataclass(frozen=True)
class GridWithResults(ContainerMixin):
    grid: GridContainer
    results: GridResultContainer

    @property
    def participants(self):
        return self.grid.participants

    @property
    def raw_grid(self):
        return self.grid.raw_grid

    @property
    def primary_data(self):
        return self.grid.primary_data

    @property
    def nodes(self):
        return self.grid.nodes

    @property
    def lines(self):
        return self.grid.lines

    @property
    def transformers_2_w(self):
        return self.grid.transformers_2_w

    @property
    def switches(self):
        return self.grid.switches

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

    @property
    def raw_grid_res(self):
        return self.results.raw_grid

    @property
    def nodes_res(self):
        return self.raw_grid_res.nodes

    @property
    def lines_res(self):
        return self.raw_grid_res.lines

    @property
    def transformers_2_w_res(self):
        return self.raw_grid_res.transformers_2w

    @property
    def switches_res(self):
        return self.raw_grid_res.switches

    @property
    def congestions_res(self):
        return self.results.raw_grid.congestions

    @property
    def participants_res(self):
        return self.results.participants

    @property
    def ems_res(self):
        return self.participants_res.ems

    @property
    def loads_res(self):
        return self.participants_res.loads

    @property
    def fixed_feed_ins_res(self):
        return self.participants_res.fixed_feed_ins

    @property
    def pvs_res(self):
        return self.participants_res.pvs

    @property
    def wecs_res(self):
        return self.participants_res.wecs

    @property
    def storages_res(self):
        return self.participants_res.storages

    @property
    def evs_res(self):
        return self.participants_res.evs

    @property
    def evcs_res(self):
        return self.participants_res.evcs

    @property
    def hps_res(self):
        return self.participants_res.hps

    @property
    def flex_res(self):
        return self.participants_res.flex

    def nodal_energies(self) -> dict[str, float]:
        return {uuid: self.nodal_energy(uuid) for uuid in self.grid.nodes.uuid}

    def to_list(self, include_empty: bool = False) -> list:
        elems = [self.grid, self.results]
        return elems if include_empty else [r for r in elems if r]

    def nodal_energy(self, uuid: str) -> float:
        return self.nodal_result(uuid).participants.sum().energy()

    def nodal_results(self) -> dict[str, GridResultContainer]:
        return {
            node_uuid: self.nodal_result(node_uuid)
            for node_uuid in self.grid.node_participants_map.keys()
        }

    def nodal_result(self, node_uuid: str) -> "GridResultContainer":
        node_participants = self.grid.node_participants_map[node_uuid]
        participants_uuids = node_participants.uuids()
        participants = self.participants_res.subset(participants_uuids)
        return GridResultContainer(
            raw_grid=self.raw_grid_res.nodal_result(node_uuid),
            participants=participants,
        )

    def em_results(
        self,
    ) -> list[Tuple[SystemParticipantsContainer, SystemParticipantsResultContainer]]:
        uuid_to_connected_asset = self.ems.uuid_to_connected_assets()
        return [
            (
                self.participants.subset(connected_assets + [em_uuid]),
                self.participants_res.subset(connected_assets + [em_uuid]),
            )
            for (em_uuid, connected_assets) in uuid_to_connected_asset.items()
        ]

    def build_extended_nodes_result(self) -> ComplexVoltagePowerDict:
        """
        Builds extended nodes result by calculation the complex power using the grids
        admittance matrix and the complex nodal voltages.
        """
        uuid_to_idx = {uuid: idx for idx, uuid in enumerate(self.nodes.uuid.to_list())}
        uuid_order = [
            x[0] for x in sorted(list(uuid_to_idx.items()), key=lambda x: x[1])
        ]

        voltage_levels = self.nodes.v_rated.value_counts()
        if len(voltage_levels) > 2:
            raise NotImplementedError(
                f"Only implemented for two voltage levels {len(voltage_levels)}"
            )
        lv_voltage = voltage_levels.index[0]

        Y = self.raw_grid.admittance_matrix(uuid_to_idx)
        v_complex = self.nodes_res.v_complex(lv_voltage, favor_ids=False)  # type: ignore
        v_complex = v_complex.reindex(columns=uuid_order)
        i = v_complex @ Y
        i.columns = v_complex.columns
        s: pd.DataFrame = -(v_complex * np.conj(i))

        ext_nodes_results = {}
        nodes_res = self.nodes_res
        for uuid, node_res in nodes_res.items():
            node_s = s[uuid]  # type: ignore
            # power values below 1e-9 are most likel a result of float calculation imprecision
            node_p = node_s.apply(lambda x: x.real if abs(x.real) > 1e-9 else 0.0)
            node_q = node_s.apply(lambda x: x.imag if abs(x.imag) > 1e-9 else 0.0)
            ext_node_res_data = node_res.data.copy()
            ext_node_res_data["p"] = node_p
            ext_node_res_data["q"] = node_q
            ext_node_res = ComplexVoltagePower(
                ext_node_res_data,
            )
            ext_nodes_results[uuid] = ext_node_res
        return ComplexVoltagePowerDict(
            ext_nodes_results,
        )

    def find_participant_result_pair(self, uuid: str):
        return self.grid.participants.find_participant(
            uuid
        ), self.participants_res.find_participant_result(uuid)

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return GridWithResults(
            self.grid.filter_by_date_time(time), self.results.filter_by_date_time(time)
        )

    def interval(self, start: datetime, end: datetime):
        return GridWithResults(self.grid, self.results.interval(start, end))

    def plot_grid(
        self,
        node_highlights: Optional[Union[dict[RGB, list[str]], list[str]]] = None,
        line_highlights: Optional[Union[dict[RGB, list[str]], list[str]]] = None,
        highlight_disconnected: Optional[bool] = False,
    ):
        return self.grid.plot(node_highlights, line_highlights, highlight_disconnected)

    def to_csv(
        self,
        grid_path: str,
        result_path: str,
        mkdirs=False,
        delimiter: str = ",",
        include_primary_data: bool = True,
    ) -> None:
        self.grid.to_csv(
            grid_path,
            include_primary_data=include_primary_data,
            mkdirs=mkdirs,
            delimiter=delimiter,
        )
        self.results.to_csv(result_path, delimiter=delimiter, mkdirs=mkdirs)

    @classmethod
    def from_csv(
        cls,
        grid_path: str | Path,
        result_path: str | Path,
        grid_delimiter: str | None = None,
        result_delimiter: str | None = None,
        primary_data_delimiter: Optional[str] = None,
        simulation_end: Optional[datetime] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ) -> "GridWithResults":
        check_filter(filter_start, filter_end)

        logger.info(f"Reading grid from {grid_path}")

        if not primary_data_delimiter:
            primary_data_delimiter = grid_delimiter

        grid = GridContainer.from_csv(
            grid_path, grid_delimiter, primary_data_delimiter=primary_data_delimiter
        )

        if not grid:
            raise ValueError(f"Grid is empty. Is the path correct? {grid_path}")

        logger.info(f"Reading results from {result_path}")

        results = GridResultContainer.from_csv(
            result_path,
            result_delimiter,
            simulation_end,
            grid_container=grid,
            filter_start=filter_start,
            filter_end=filter_end,
        )

        if not results:
            raise ValueError(f"Results are empty. Is the path correct? {result_path}")

        return (
            GridWithResults(grid, results)
            if not filter_start
            else GridWithResults(grid, results)
        )

    @classmethod
    def entity_keys(cls):
        return set()

    @classmethod
    def empty(cls):
        return GridWithResults(GridContainer.empty(), GridResultContainer.empty())

    @staticmethod
    def _calc_complex_power(uuid, nodal_result: GridResultContainer):
        """
        NOTE: Utility function for parallel processing of building ExtendedNodesResult
        """
        complex_power = nodal_result.participants.sum()
        return uuid, complex_power
