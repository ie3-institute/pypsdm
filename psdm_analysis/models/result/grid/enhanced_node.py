from dataclasses import dataclass
from datetime import datetime
from typing import Dict

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.models.input.enums import RawGridElementsEnum
from psdm_analysis.models.result.grid.node import NodeResult, NodesResult
from psdm_analysis.processing.dataframe import filter_data_for_time_interval


@dataclass(frozen=True)
class EnhancedNodeResult(NodeResult):
    def __eq__(self, other):
        if not isinstance(other, EnhancedNodeResult):
            return False
        return (
            (self.input_model == other.input_model)
            & (self.name == other.name)
            & (self.data.equals(other.data))
        )

    @classmethod
    def from_node_result(
        cls, node_res: NodeResult, p: Series, q: Series = None
    ) -> "EnhancedNodeResult":
        return cls(
            RawGridElementsEnum.NODE,
            node_res.name,
            node_res.input_model,
            pd.concat([node_res.data, p.rename("p"), q.rename("q")], axis=1),
        )

    def filter_for_time_interval(self, start: datetime, end: datetime):
        filtered_data = filter_data_for_time_interval(self.data, start, end)
        return EnhancedNodeResult.build(self.input_model, filtered_data, self.name)

    @property
    def p(self) -> Series:
        return self.data["p"]

    @property
    def q(self) -> Series:
        return self.data["q"]


# todo: This should inherit from ResultDict -> rename participants and nodes to entities
@dataclass(frozen=True)
class EnhancedNodesResult(NodesResult):
    entities: Dict[str, EnhancedNodeResult]

    @classmethod
    def from_nodes_result(
        cls, nodes_result: NodesResult, ps: dict[str:Series], qs: dict[str:Series]
    ):
        return cls(
            RawGridElementsEnum.NODE,
            {
                uuid: EnhancedNodeResult.from_node_result(result, ps[uuid], qs[uuid])
                for uuid, result in nodes_result.entities.items()
            },
        )

    @property
    def p(self) -> DataFrame:
        return pd.concat(
            [
                node_res.p.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        ).sort_index()

    @property
    def q(self) -> DataFrame:
        return pd.concat(
            [
                node_res.q.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        ).sort_index()

    def filter(self, uuids: set[str]):
        return EnhancedNodesResult({uuid: self.entities[uuid] for uuid in uuids})
