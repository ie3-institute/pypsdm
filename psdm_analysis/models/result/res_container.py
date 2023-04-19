from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Set

from psdm_analysis.io.utils import check_filter
from psdm_analysis.models.result.grid.node import NodesResult
from psdm_analysis.models.result.participant.participants_res_container import (
    ParticipantsResultContainer,
)


@dataclass(frozen=True)
class ResultContainer:
    name: str
    nodes: NodesResult
    participants: ParticipantsResultContainer

    def __len__(self):
        return len(self.nodes) + len(self.participants)

    # todo: implement slicing
    def __getitem__(self, slice_val):
        raise NotImplementedError

    @classmethod
    def from_csv(
        cls,
        name: str,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: Optional[datetime] = None,
        from_agg_results: bool = True,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ):
        check_filter(filter_start, filter_end)
        # todo: load async
        nodes = NodesResult.from_csv(
            simulation_data_path,
            delimiter,
            simulation_end,
            filter_start=filter_start,
            filter_end=filter_end,
        )

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
            from_agg_results=from_agg_results,
            filter_start=filter_start,
            filter_end=filter_end,
        )

        return cls(name, nodes, participants)

    def uuids(self) -> set[str]:
        return set(self.nodes.entities.keys())

    # todo: implement
    def filter_by_nodes(self, nodes: Set[str]):
        pass

    def filter_for_time_interval(self, start: datetime, end: datetime):
        return ResultContainer(
            self.name,
            self.nodes.filter_for_time_interval(start, end),
            self.participants.filter_for_time_interval(start, end),
        )
