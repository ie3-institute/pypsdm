import concurrent.futures
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from pypsdm.io.utils import check_filter
from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.input.container.grid import GridContainer
from pypsdm.models.input.container.mixins import ContainerMixin
from pypsdm.models.result.grid.connector import ConnectorsResult
from pypsdm.models.result.grid.line import LinesResult
from pypsdm.models.result.grid.node import NodesResult
from pypsdm.models.result.grid.switch import SwitchesResult
from pypsdm.models.result.grid.transformer import Transformers2WResult


@dataclass(frozen=True)
class RawGridResultContainer(ContainerMixin):
    nodes: NodesResult
    lines: LinesResult
    transformers_2w: ConnectorsResult
    switches: SwitchesResult

    def __len__(self):
        return (
            +len(self.nodes)
            + len(self.lines)
            + len(self.transformers_2w)
            + len(self.switches)
        )

    # TODO: implement slicing
    def __getitem__(self, slice_val):
        raise NotImplementedError

    def to_list(self, include_empty: bool = False) -> list:
        res = [
            self.nodes,
            self.lines,
            self.transformers_2w,
            self.switches,
        ]
        return res if include_empty else [r for r in res if r]

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return RawGridResultContainer(
            self.nodes.filter_by_date_time(time),
            self.lines.filter_by_date_time(time),
            self.transformers_2w.filter_by_date_time(time),
            self.switches.filter_by_date_time(time),
        )

    def filter_for_time_interval(self, start: datetime, end: datetime):
        return RawGridResultContainer(
            self.nodes.filter_for_time_interval(start, end),
            self.lines.filter_for_time_interval(start, end),
            self.transformers_2w.filter_for_time_interval(start, end),
            self.switches.filter_for_time_interval(start, end),
        )

    def concat(self, other: "RawGridResultContainer", deep: bool = True, keep="last"):
        """
        Concatenates the data of the two containers, which means concatenating
        the data of their entities.

        NOTE: This only makes sense if the entities indexes are continuous. Given
        that we deal with discrete event data that means that the last state of self
        is valid until the first state of other. Which would probably not be what
        you want in case the results are separated by a year.

        Args:
            other: The other GridResultContainer object to concatenate with.
            deep: Whether to do a deep copy of the data.
            keep: How to handle duplicate indexes. "last" by default.
        """
        return RawGridResultContainer(
            self.nodes.concat(other.nodes, deep=deep, keep=keep),
            self.lines.concat(other.lines, deep=deep, keep=keep),
            self.transformers_2w.concat(other.transformers_2w, deep=deep, keep=keep),
            self.switches.concat(other.switches, deep=deep, keep=keep),
        )

    def nodal_result(self, node_uuid: str) -> "RawGridResultContainer":
        if node_uuid not in self.nodes:
            return RawGridResultContainer.create_empty()
        return RawGridResultContainer(
            nodes=NodesResult(
                {node_uuid: self.nodes[node_uuid]},
            ),
            lines=LinesResult({}),
            transformers_2w=Transformers2WResult({}),
            switches=SwitchesResult({}),
        )

    @classmethod
    def from_csv(
        cls,
        simulation_data_path: str,
        delimiter: str | None = None,
        simulation_end: Optional[datetime] = None,
        grid_container: Optional[GridContainer] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ):
        check_filter(filter_start, filter_end)

        res_files = [
            f for f in os.listdir(simulation_data_path) if f.endswith("_res.csv")
        ]
        if len(res_files) == 0:
            raise FileNotFoundError(
                f"No simulation results found in '{simulation_data_path}'."
            )

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
                LinesResult.from_csv,
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
            if len(nodes) == 0:
                raise ValueError(
                    "Can't determine simulation end time automatically. No node results to base it on. Please configure 'simulation_end' manually."
                )
            some_node_res = next(iter(nodes.values()))
            simulation_end = some_node_res.data.index.max()

        return cls(nodes, lines, transformers_2_w, switches)

    @classmethod
    def create_empty(cls):
        return cls(
            nodes=NodesResult({}),
            lines=LinesResult({}),
            transformers_2w=Transformers2WResult({}),
            switches=SwitchesResult({}),
        )
