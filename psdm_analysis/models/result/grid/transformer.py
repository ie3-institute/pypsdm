from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

import numpy as np
from pandas import Series

from psdm_analysis.models.result.grid.connector import ConnectorResult, ConnectorsResult

if TYPE_CHECKING:
    from psdm_analysis.models.gwr import GridWithResults


@dataclass(frozen=True)
class Transformer2WResult(ConnectorResult):
    @property
    def tap_pos(self) -> Series:
        return self.data["tap_pos"]

    def calc_apparent_power_gwr(self, gwr: GridWithResults, side="hv"):
        transformer = gwr.grid.raw_grid.transformers_2_w.subset(self.input_model)
        node_uuid = transformer.node_a if side == "hv" else transformer.node_b
        node_uuid = node_uuid.to_list()[0]
        v_rated = gwr.grid.raw_grid.nodes.v_rated.loc[node_uuid]
        node_res = gwr.results.nodes[node_uuid]
        node_side = self._get_node_for_side(side)
        return self.calc_apparent_power(
            node_res, voltage_level_kv=v_rated, node=node_side
        )

    def calc_active_power_gwr(self, gwr: GridWithResults, side="hv"):
        s = self.calc_apparent_power_gwr(gwr, side)
        return s.apply(lambda x: np.real(x))

    def calc_reactive_power_gwr(self, gwr: GridWithResults, side="hv"):
        s = self.calc_apparent_power_gwr(gwr, side)
        return s.apply(lambda x: np.imag(x))

    def calc_transformer_utilisation(self, gwr: GridWithResults, side="hv"):
        transformer = gwr.grid.raw_grid.transformers_2_w.subset(self.input_model)
        s_rated = transformer.s_rated.to_list()[0]
        return (
            self.calc_apparent_power_gwr(gwr, side).apply(lambda x: np.abs(x)) / s_rated
        )

    @staticmethod
    def attributes() -> List[str]:
        return ConnectorResult.attributes() + ["tap_pos"]

    @staticmethod
    def _get_node_for_side(side):
        if side == "hv":
            return "a"
        elif side == "lv":
            return "b"
        else:
            raise ValueError('Side has to be either "hv" or "lv"')


@dataclass(frozen=True)
class Transformers2WResult(ConnectorsResult):
    entities: dict[str, Transformer2WResult]
