from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

import numpy as np
import pandas as pd
from pandas import Series

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.grid.connector import ConnectorResult, ConnectorsResult
from pypsdm.models.result.power import PQResult

if TYPE_CHECKING:
    from pypsdm.models.gwr import GridWithResults


@dataclass(frozen=True)
class Transformer2WResult(ConnectorResult):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

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
            node_res, voltage_level_kv=v_rated, node=node_side  # type: ignore
        )

    def calc_active_power_gwr(self, gwr: GridWithResults, side="hv"):
        s = self.calc_apparent_power_gwr(gwr, side)
        return s.apply(lambda x: np.real(x)).rename("p")

    def calc_reactive_power_gwr(self, gwr: GridWithResults, side="hv"):
        s = self.calc_apparent_power_gwr(gwr, side)
        return s.apply(lambda x: np.imag(x)).rename("q")

    def calc_transformer_utilisation(self, gwr: GridWithResults, side="hv"):
        transformer = gwr.grid.raw_grid.transformers_2_w.subset(self.input_model)
        s_rated = transformer.s_rated.to_list()[0]
        return (
            self.calc_apparent_power_gwr(gwr, side).apply(lambda x: np.abs(x)) / s_rated
        )

    def to_pq_result(self, gwr: GridWithResults, side="hv"):
        p = self.calc_active_power_gwr(gwr, side)
        q = self.calc_reactive_power_gwr(gwr, side)
        data = pd.concat([p, q], axis=1)
        return PQResult(self.entity_type, self.input_model, self.name, data)

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


class Transformers2WResult(ConnectorsResult):

    def __init__(self, data: dict[str, Transformer2WResult]):
        super().__init__(RawGridElementsEnum.TRANSFORMER_2_W, data)
