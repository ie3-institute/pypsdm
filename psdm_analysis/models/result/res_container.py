from dataclasses import dataclass
from datetime import datetime
from typing import Set

from psdm_analysis.models.input.container.grid_container import RawGridContainer
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
        pass

    @classmethod
    def from_csv(
        cls,
        name: str,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime = None,
        grid_data: RawGridContainer = None,
        from_agg_results: bool = True,
    ):
        node_input = grid_data.nodes if grid_data else None
        nodes = NodesResult.from_csv(simulation_data_path, delimiter, node_input)

        if simulation_end is None:
            some_node_res = next(iter(nodes.nodes.values()))
            simulation_end = some_node_res.end

        participants = ParticipantsResultContainer.from_csv(
            simulation_data_path,
            delimiter,
            simulation_end,
            from_agg_results=from_agg_results,
        )

        return cls(name, nodes, participants)

    def uuids(self) -> set[str]:
        return set(self.nodes.nodes.keys())

    # todo: implement
    def filter_by_nodes(self, nodes: Set[str]):
        pass
