import concurrent.futures
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from pypsdm.io.utils import check_filter
from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.input.container.grid import GridContainer
from pypsdm.models.input.container.mixins import ContainerMixin
from pypsdm.models.result.container.participants import ParticipantsResultContainer
from pypsdm.models.result.grid.connector import ConnectorsResult
from pypsdm.models.result.grid.node import NodesResult
from pypsdm.models.result.grid.switch import SwitchesResult
from pypsdm.models.result.grid.transformer import Transformers2WResult


@dataclass(frozen=True)
class GridResultContainer(ContainerMixin):
    name: str
    nodes: NodesResult
    lines: ConnectorsResult
    transformers_2w: ConnectorsResult
    switches: SwitchesResult
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

    def to_list(self, include_empty: bool = False) -> list:
        res = [self.nodes, self.lines, self.transformers_2w, self.participants]
        return res if include_empty else [r for r in res if r]

    def uuids(self) -> set[str]:
        return set(self.nodes.entities.keys())

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return GridResultContainer(
            self.name,
            self.nodes.filter_by_date_time(time),
            self.lines.filter_by_date_time(time),
            self.transformers_2w.filter_by_date_time(time),
            self.switches.filter_by_date_time(time),
            self.participants.filter_by_date_time(time),
        )

    def filter_for_time_interval(self, start: datetime, end: datetime):
        return GridResultContainer(
            self.name,
            self.nodes.filter_for_time_interval(start, end),
            self.lines.filter_for_time_interval(start, end),
            self.transformers_2w.filter_for_time_interval(start, end),
            self.switches.filter_for_time_interval(start, end),
            self.participants.filter_for_time_interval(start, end),
        )

    def to_csv(self, path: str, delimiter: str = ",", mkdirs: bool = False):
        for res in self.to_list(include_empty=False):
            res.to_csv(path, delimiter=delimiter, mkdirs=mkdirs)

    @classmethod
    def from_csv(
        cls,
        name: str,
        simulation_data_path: str,
        delimiter: str | None = None,
        simulation_end: Optional[datetime] = None,
        grid_container: Optional[GridContainer] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ):
        check_filter(filter_start, filter_end)

        with concurrent.futures.ProcessPoolExecutor() as executor:
            nodes_future = executor.submit(
                NodesResult.from_csv,
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
            switches_future = executor.submit(
                SwitchesResult.from_csv,
                simulation_data_path,
                delimiter,
                simulation_end,
                grid_container.raw_grid.switches if grid_container else None,
                filter_start,
                filter_end,
            )

            nodes = nodes_future.result()
            transformers_2_w = transformers_2_w_future.result()
            lines = lines_future.result()
            switches = switches_future.result()

        if simulation_end is None:
            if len(nodes.entities) == 0:
                raise ValueError(
                    "Can't determine simulation end time automatically. No node results to base it on. Please configure 'simulation_end' manually."
                )
            some_node_res = next(iter(nodes.entities.values()))
            simulation_end = some_node_res.data.index.max()

        participants = ParticipantsResultContainer.from_csv(
            simulation_data_path,
            simulation_end,  # type: ignore
            grid_container=grid_container,
            filter_start=filter_start,
            filter_end=filter_end,
            delimiter=delimiter,
        )

        return cls(name, nodes, lines, transformers_2_w, switches, participants)

    @classmethod
    def create_empty(cls):
        return cls(
            name="Empty Container",
            nodes=NodesResult.create_empty(RawGridElementsEnum.NODE),
            lines=ConnectorsResult.create_empty(RawGridElementsEnum.LINE),
            transformers_2w=ConnectorsResult.create_empty(
                RawGridElementsEnum.TRANSFORMER_2_W
            ),
            participants=ParticipantsResultContainer.create_empty(),
        )
