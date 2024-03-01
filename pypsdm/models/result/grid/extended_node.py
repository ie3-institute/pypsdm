from dataclasses import dataclass

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.grid.node import NodeResult, NodesResult
from pypsdm.models.result.power import PQResult


@dataclass(frozen=True)
class ExtendedNodeResult(NodeResult):
    def __eq__(self, other):
        if not isinstance(other, ExtendedNodeResult):
            return False
        return (
            (self.input_model == other.input_model)
            & (self.name == other.name)
            & (self.data.equals(other.data))
        )

    @property
    def p(self) -> Series:
        return self.data["p"]

    @property
    def q(self) -> Series:
        return self.data["q"]

    @classmethod
    def from_node_result(
        cls, node_res: NodeResult, pq: PQResult
    ) -> "ExtendedNodeResult":
        if pq:
            # First time step of nodal voltages will most likely be nan because SIMONA pf calculation
            # starts at t+1. In this case we drop the time step.
            data = (
                pd.concat([node_res.data, pq.data], axis=1)
                .sort_index()
                .ffill()
                .dropna()
            )
        else:
            data = node_res.data.copy()
            data["p"] = np.nan
            data["q"] = np.nan
        return cls(
            RawGridElementsEnum.NODE,
            node_res.input_model,
            node_res.name,
            data,
        )


@dataclass(frozen=True)
class ExtendedNodesResult(NodesResult):
    entities: dict[str, ExtendedNodeResult]

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

    @classmethod
    def from_nodes_result(
        cls, nodes_result: NodesResult, nodal_pq: dict[str, PQResult]
    ):
        return cls(
            RawGridElementsEnum.NODE,
            {
                uuid: ExtendedNodeResult.from_node_result(result, nodal_pq[uuid])
                for uuid, result in nodes_result.entities.items()
            },
        )
