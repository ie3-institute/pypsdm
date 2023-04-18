from dataclasses import dataclass
from datetime import datetime
from typing import Set

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
        simulation_end: datetime = None,
        from_agg_results: bool = True,
    ):
        nodes = NodesResult.from_csv(simulation_data_path, delimiter, simulation_end)

        if simulation_end is None:
            some_node_res = next(iter(nodes.nodes.values()))
            # todo: this only works if we can guarantee order
            simulation_end = some_node_res.data.iloc[-1].name

        participants = ParticipantsResultContainer.from_csv(
            simulation_data_path,
            delimiter,
            simulation_end,
            from_agg_results=from_agg_results,
        )

        return cls(name, nodes, participants)

    def uuids(self) -> set[str]:
        return set(self.nodes.entities.keys())

    # todo: implement
    def filter_by_nodes(self, nodes: Set[str]):
        pass
