from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from pandas import Series

from psdm_analysis.models.result.grid.connector import ConnectorResult, ConnectorsResult

if TYPE_CHECKING:
    from psdm_analysis.models.gwr import GridWithResults


@dataclass(frozen=True)
class Transformer2WResult(ConnectorResult):
    @property
    def tap_pos(self) -> Series:
        return self.data["tap_pos"]

    def calc_rated_power_gwr(self, gwr: GridWithResults, side="hv", absolute=True):
        if side == "hv":
            node = "a"
        elif side == "lv":
            node = "b"
        else:
            raise ValueError('Side has to be either "hv" or "lv"')
        transformer = gwr.grid.raw_grid.transformers_2_w.subset(self.input_model)
        node_uuid = transformer.node_a if side == "hv" else transformer.node_b
        node_uuid = node_uuid.to_list()[0]
        v_rated = gwr.grid.raw_grid.nodes.v_rated.loc[node_uuid]
        node_res = gwr.results.nodes[node_uuid]
        return self.calc_rated_power(node_res, v_rated, node, absolute)

    def calc_transformer_utilisation(
        self, gwr: GridWithResults, side="hv", absolute=True
    ):
        transformer = gwr.grid.raw_grid.transformers_2_w.subset(self.input_model)
        # todo: adjust to real prefix
        s_rated = transformer.s_rated.to_list()[0]
        return self.calc_rated_power_gwr(gwr, side, absolute) / s_rated

    @staticmethod
    def attributes() -> List[str]:
        return ConnectorResult.attributes() + ["tap_pos"]


@dataclass(frozen=True)
class Transformers2WResult(ConnectorsResult):
    entities: dict[str, Transformer2WResult]
