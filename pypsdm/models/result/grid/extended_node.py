from dataclasses import dataclass

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.grid.node import NodeResult, NodesResult
from pypsdm.models.result.power import PQResult


@dataclass(frozen=True)
class ExtendedNodeResult(NodeResult):
    """
    Extends the node result with power values p and q.
    Can be calculated using `GridWithResults.build_extended_nodes_result`
    """

    @property
    def v_mag(self) -> Series:
        return self.data["v_mag"].dropna()

    @property
    def v_ang(self) -> Series:
        return self.data["v_ang"].dropna()

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

    @property
    def s(self) -> Series:
        return self.p + 1j * self.q

    @classmethod
    def from_node_result(
        cls,
        node_res: NodeResult,
        pq: PQResult,
        fill_zero: bool = False,
    ) -> "ExtendedNodeResult":
        """
        Creates an ExtendedNodeResult from a NodeResult and a PQResult.

        Args:
            node_res: The NodeResult to extend
            pq: The PQResult to extend the NodeResult with
            fill_zero: Wether to fill the power values with zero if no power
                values are present. Otherwise nan is used.
        """

        if pq:
            data = pd.concat([node_res.data, pq.data], axis=1).sort_index().dropna()
        else:
            data = node_res.data.copy()
            if fill_zero:
                data["p"] = 0
                data["q"] = 0
            else:
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
    entities: dict[str, ExtendedNodeResult]  # type: ignore

    def p(self) -> DataFrame:
        data = pd.concat(
            [
                node_res.p.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        ).sort_index()
        return data

    def q(self) -> DataFrame:
        data = pd.concat(
            [
                node_res.q.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        ).sort_index()
        return data

    def s(self) -> DataFrame:
        data = pd.concat(
            [
                node_res.s.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        ).sort_index()
        return data

    @classmethod
    def from_nodes_result(
        cls,
        nodes_result: NodesResult,
        nodal_pq: dict[str, PQResult],
        fill_zero: bool = False,
    ):
        if nodes_result:
            return cls(
                RawGridElementsEnum.NODE,
                {
                    uuid: ExtendedNodeResult.from_node_result(
                        result, nodal_pq[uuid], fill_zero
                    )
                    for uuid, result in nodes_result.entities.items()
                },
            )
        else:
            entities = {}
            for uuid, pq_res in nodal_pq.items():
                data = pq_res.data
                data["v_mag"] = np.nan
                data["v_ang"] = np.nan
                entity = ExtendedNodeResult(RawGridElementsEnum.NODE, uuid, None, data)
                entities[uuid] = entity
            return cls(RawGridElementsEnum.NODE, entities)
