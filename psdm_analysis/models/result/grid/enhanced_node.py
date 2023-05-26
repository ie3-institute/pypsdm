from dataclasses import dataclass

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.models.input.enums import RawGridElementsEnum
from psdm_analysis.models.result.grid.node import NodeResult, NodesResult
from psdm_analysis.models.result.power import PQResult


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
        cls, node_res: NodeResult, pq: PQResult
    ) -> "EnhancedNodeResult":
        return cls(
            RawGridElementsEnum.NODE,
            node_res.input_model,
            node_res.name,
            pd.concat([node_res.data, pq.data], axis=1).sort_index(),
        )

    @property
    def p(self) -> Series:
        return self.data["p"]

    @property
    def q(self) -> Series:
        return self.data["q"]


@dataclass(frozen=True)
class EnhancedNodesResult(NodesResult):
    entities: dict[str, EnhancedNodeResult]

    @classmethod
    def from_nodes_result(
        cls, nodes_result: NodesResult, nodal_pq: dict[str, PQResult]
    ):
        return cls(
            RawGridElementsEnum.NODE,
            {
                uuid: EnhancedNodeResult.from_node_result(result, nodal_pq[uuid])
                for uuid, result in nodes_result.entities.items()
            },
        )

    @property
    def p(self) -> DataFrame:
        return (
            pd.concat(
                [
                    node_res.p.rename(node_res.input_model)
                    for node_res in self.entities.values()
                ],
                axis=1,
            )
            .sort_index()
            .ffill()
            .fillna(0)
        )

    @property
    def q(self) -> DataFrame:
        return (
            pd.concat(
                [
                    node_res.q.rename(node_res.input_model)
                    for node_res in self.entities.values()
                ],
                axis=1,
            )
            .sort_index()
            .ffill()
            .fillna(0)
        )
