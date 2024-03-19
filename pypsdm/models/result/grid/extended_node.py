from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.grid.node import NodeResult, NodesResult
from pypsdm.models.result.power import PQResult


@dataclass(frozen=True)
class ExtendedNodeResult(NodeResult):
    __data_pf: DataFrame | None = field(default=None, init=False, repr=False)

    # TODO: This is quite slow for large datasets.
    def data_pf(
        self, cache_result: bool = True, use_cache: bool = True
    ) -> pd.DataFrame:
        """
        When the resolution of the participants power is different
        than the resolution of the power flow, SIMONA uses the average power of
        each participant since the last power flow as the basis for the current
        power flow calculation. If the pf has the same resolution as the
        participants state changes, the power flow calculation is done before
        the state changes occur. That means given a 15 minute resolution for
        both the power flow and e.g. a load the power flow calculation at
        12:00 uses the power of the load from 11:45 and so on.

        `data_pf` calculates the power that the power flow calculation would have used
        and synchronize the time steps. Each resulting power value at a time step
        therefore corresponts to the average power of all participants since the last
        time step. All time steps where no pf calculation was done (i.e. there are no
        voltage values for the time step) are dropped.

        As this is a quite expensive operation, the result is cached by default.
        NOTE: Keep in mind that for the cached result to stay valid, the underlying
        data must not change. Set `use_cache` to False to recalculate the result.

        Args:
            cache_result: Whether to cache the result
            use_cache: Whether to use the cached result if available
        """
        if self.__data_pf is not None and use_cache:
            return self.__data_pf

        data = self.data.copy()
        if not data.index.is_monotonic_increasing:
            data = data.sort_index()

        dur_col = (
            (data.index[1::] - data.index[:-1])
            .to_series()
            .apply(lambda x: x.total_seconds() / 3600)
            .reset_index(drop=True)
        )
        dur_col[data.index[-1]] = 0
        dur_col.index = data.index
        dur_col[data.index[-1]] = 0
        data["duration"] = dur_col

        p, q = 0, 0
        acc_duration = 0

        for i, (dt, row) in enumerate(data.iterrows()):  # type: ignore
            if np.isnan(row["v_mag"]):
                duration = row["duration"]
                p += row["p"] * duration
                q += row["q"] * duration
                acc_duration += duration
            else:
                row_p = row["p"]
                row_q = row["q"]

                if acc_duration == 0:
                    if i == 0:
                        data.loc[dt, "p"] = 0  # type: ignore
                        data.loc[dt, "q"] = 0  # type: ignore
                    else:
                        raise ValueError(
                            "There was no time between consecutive power flow calculations. This is should not happen."
                        )
                else:
                    data.loc[dt, "p"] = p / acc_duration  # type: ignore
                    data.loc[dt, "q"] = q / acc_duration  # type: ignore

                duration = row["duration"]
                p, q = row_p * duration, row_q * duration
                acc_duration = row["duration"]
        data = data.dropna().drop(columns=["duration"])
        # bypass frozen dataclass
        if cache_result:
            object.__setattr__(self, "_ExtendedNodeResult__data_pf", data)
        return data

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

    def p_pf(self) -> Series:
        """
        Returns the power values that would have been used in the power flow calculation
        which are averaged inbetween power flow calculations. See `data_pf` for more
        details.
        """
        return self.data_pf()["p"]

    @property
    def q(self) -> Series:
        return self.data["q"]

    def q_pf(self) -> Series:
        """
        Returns the power values that would have been used in the power flow calculation
        which are averaged inbetween power flow calculations. See `data_pf` for more
        details.
        """
        return self.data_pf()["q"]

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

    def p_pf(self):
        """
        Returns the power values that would have been used in the power flow calculation
        which are averaged inbetween power flow calculations. See `data_pf` for more
        details.
        """
        data = pd.concat(
            [
                node_res.p_pf().rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        ).sort_index()
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

    def q_pf(self):
        """
        Returns the power values that would have been used in the power flow calculation
        which are averaged inbetween power flow calculations. See `data_pf` for more
        details.
        """
        data = pd.concat(
            [
                node_res.q_pf().rename(node_res.input_model)
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
