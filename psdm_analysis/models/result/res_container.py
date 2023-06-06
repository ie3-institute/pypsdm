import concurrent.futures
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from psdm_analysis.io.utils import check_filter
from psdm_analysis.models.input.container.grid_container import GridContainer
from psdm_analysis.models.input.enums import RawGridElementsEnum
from psdm_analysis.models.result.grid.connector import ConnectorsResult
from psdm_analysis.models.result.grid.node import NodesResult
from psdm_analysis.models.result.grid.transformer import Transformers2WResult
from psdm_analysis.models.result.participant.participants_res_container import (
    ParticipantsResultContainer,
)


@dataclass(frozen=True)
class ResultContainer:
    name: str
    nodes: NodesResult
    lines: ConnectorsResult
    transformers_2w: ConnectorsResult
    participants: ParticipantsResultContainer

    def __len__(self):
        return (
            len(self.nodes)
            + len(self.lines)
            + len(self.transformers_2w)
            + len(self.participants)
        )

    # todo: implement slicing
    def __getitem__(self, slice_val):
        raise NotImplementedError

    def uuids(self) -> set[str]:
        return set(self.nodes.entities.keys())

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return ResultContainer(
            self.name,
            self.nodes.filter_by_date_time(time),
            self.lines.filter_by_date_time(time),
            self.transformers_2w.filter_by_date_time(time),
            self.participants.filter_by_date_time(time),
        )

    def filter_for_time_interval(self, start: datetime, end: datetime):
        return ResultContainer(
            self.name,
            self.nodes.filter_for_time_interval(start, end),
            self.lines.filter_for_time_interval(start, end),
            self.transformers_2w.filter_for_time_interval(start, end),
            self.participants.filter_for_time_interval(start, end),
        )

    @classmethod
    def from_csv(
        cls,
        name: str,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: Optional[datetime] = None,
        grid_container: Optional[GridContainer] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ):
        check_filter(filter_start, filter_end)

        with concurrent.futures.ProcessPoolExecutor() as executor:
            nodes_future = executor.submit(
                NodesResult.from_csv,
                RawGridElementsEnum.NODE,
                simulation_data_path,
                delimiter,
                simulation_end,
                grid_container.raw_grid.nodes if grid_container else None,
                filter_start,
                filter_end,
            )
            transformers_2_w_future = executor.submit(
                Transformers2WResult.from_csv,
                RawGridElementsEnum.TRANSFORMER_2_W,
                simulation_data_path,
                delimiter,
                simulation_end,
                grid_container.raw_grid.transformers_2_w if grid_container else None,
                filter_start,
                filter_end,
            )
            lines_future = executor.submit(
                ConnectorsResult.from_csv,
                RawGridElementsEnum.LINE,
                simulation_data_path,
                delimiter,
                simulation_end,
                grid_container.raw_grid.lines if grid_container else None,
                filter_start,
                filter_end,
            )

            nodes = nodes_future.result()
            transformers_2_w = transformers_2_w_future.result()
            lines = lines_future.result()

        if simulation_end is None:
            if len(nodes.entities) == 0:
                raise ValueError(
                    "Can't determine simulation end time. No node results to base it on."
                )
            some_node_res = next(iter(nodes.entities.values()))
            simulation_end = some_node_res.data.index.max()

        participants = ParticipantsResultContainer.from_csv(
            simulation_data_path,
            delimiter,
            simulation_end,
            grid_container=grid_container,
            filter_start=filter_start,
            filter_end=filter_end,
        )

        return cls(name, nodes, lines, transformers_2_w, participants)
