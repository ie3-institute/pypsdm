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
        cls, node_res: NodeResult, pq: PQResult, fill_zero: bool = False
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
    entities: dict[str, ExtendedNodeResult]

    def p(self, ffill=True) -> DataFrame:
        """
        Returns a DataFrame with the p values of all nodes.

        NOTE: By default forward fills the resulting nan values that occur in case of
        different time resolutions of the pq results. This is valid if you are dealing
        with event discrete time series data. This might not be what you want otherwise

        Args:
            ffill: Forward fill the resulting nan values

        Returns:
            DataFrame: DataFrame with the p values of all nodes
        """
        data = pd.concat(
            [
                node_res.p.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        ).sort_index()
        if ffill:
            data = data.ffill()
        return data

    def q(self, ffill=True) -> DataFrame:
        """
        Returns a DataFrame with the q values of all nodes.

        NOTE: By default forward fills the resulting nan values that occur in case of
        different time resolutions of the pq results. This is valid if you are dealing
        with event discrete time series data. This might not be what you want otherwise

        Args:
            ffill: Forward fill the resulting nan values

        Returns:
            DataFrame: DataFrame with the q values of all nodes
        """
        data = (
            pd.concat(
                [
                    node_res.q.rename(node_res.input_model)
                    for node_res in self.entities.values()
                ],
                axis=1,
            )
            .sort_index()
            .ffill()
        )
        if ffill:
            data = data.ffill()
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
