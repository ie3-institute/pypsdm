import concurrent
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple, Union

from pypsdm.io.utils import check_filter
from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.input.container.grid import GridContainer
from pypsdm.models.input.container.mixins import ContainerMixin
from pypsdm.models.input.container.participants import SystemParticipantsContainer
from pypsdm.models.result.container.grid import GridResultContainer
from pypsdm.models.result.container.participants import ParticipantsResultContainer
from pypsdm.models.result.grid.connector import ConnectorsResult
from pypsdm.models.result.grid.enhanced_node import EnhancedNodesResult
from pypsdm.models.result.grid.node import NodesResult
from pypsdm.models.result.grid.transformer import Transformers2WResult


@dataclass(frozen=True)
class GridWithResults(ContainerMixin):
    grid: GridContainer
    results: GridResultContainer

    def nodal_energies(self) -> dict[str, float]:
        return {uuid: self.nodal_energy(uuid) for uuid in self.grid.raw_grid.nodes.uuid}

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
        participants = self.results.participants.subset(participants_uuids)
        return GridResultContainer(
            name=node_uuid,
            nodes=NodesResult(
                RawGridElementsEnum.NODE,
                {node_uuid: self.results.nodes.entities[node_uuid]},
            ),
            lines=ConnectorsResult.create_empty(RawGridElementsEnum.LINE),
            transformers_2w=Transformers2WResult.create_empty(
                RawGridElementsEnum.TRANSFORMER_2_W
            ),
            participants=participants,
        )

    def em_results(
        self,
    ) -> List[Tuple[SystemParticipantsContainer, ParticipantsResultContainer]]:
        uuid_to_connected_asset = self.grid.participants.ems.uuid_to_connected_assets()
        return [
            (
                self.grid.participants.subset(connected_assets + [em_uuid]),
                self.results.participants.subset(connected_assets + [em_uuid]),
            )
            for (em_uuid, connected_assets) in uuid_to_connected_asset.items()
        ]

    def build_enhanced_nodes_result(self):
        nodal_results = self.nodal_results()

        with ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(self.calc_pq, uuid, nodal_result)
                for uuid, nodal_result in nodal_results.items()
            }

            nodal_pq = {}
            for future in concurrent.futures.as_completed(futures):  # type: ignore
                uuid, pq = future.result()
                nodal_pq[uuid] = pq

        return EnhancedNodesResult.from_nodes_result(self.results.nodes, nodal_pq)

    def find_participant_result_pair(self, uuid: str):
        return self.grid.participants.find_participant(
            uuid
        ), self.results.participants.find_participant_result(uuid)

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return GridWithResults(
            self.grid.filter_by_date_time(time), self.results.filter_by_date_time(time)
        )

    def filter_for_time_interval(self, start: datetime, end: datetime):
        return GridWithResults(
            self.grid, self.results.filter_for_time_interval(start, end)
        )

    @classmethod
    def from_csv(
        cls,
        name: str,
        grid_path: str,
        grid_delimiter: str,
        result_path: str,
        result_delimiter: str,
        primary_data_delimiter: Optional[str] = None,
        simulation_end: Optional[datetime] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ) -> "GridWithResults":
        check_filter(filter_start, filter_end)

        if not primary_data_delimiter:
            primary_data_delimiter = grid_delimiter

        grid = GridContainer.from_csv(
            grid_path, grid_delimiter, primary_data_delimiter=primary_data_delimiter
        )

        if not grid:
            raise ValueError(f"Grid is empty. Is the path correct? {grid_path}")

        results = GridResultContainer.from_csv(
            name,
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
    def create_empty(cls):
        return GridWithResults(
            GridContainer.create_empty(), GridResultContainer.create_empty()
        )

    @staticmethod
    def calc_pq(uuid, nodal_result: GridResultContainer):
        pq = nodal_result.participants.sum()
        return uuid, pq
