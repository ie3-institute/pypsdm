from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal

import numpy as np
import pandas as pd
from pandas import Series

from pypsdm.models.enums import EntitiesEnum, RawGridElementsEnum
from pypsdm.models.result.grid.connector import ConnectorCurrent
from pypsdm.models.result.participant.dict import EntitiesResultDictMixin
from pypsdm.models.ts.base import EntityKey, K, TimeSeriesDict
from pypsdm.models.ts.types import ComplexPower

if TYPE_CHECKING:
    from pypsdm.models.gwr import GridWithResults


class Transformer2WResult(ConnectorCurrent):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @property
    def tap_pos(self) -> Series:
        return self.data["tap_pos"]

    def apparent_power(
        self,
        uuid: str | EntityKey,
        gwr: GridWithResults,
        side: Literal["hv", "lv"] = "hv",
    ):
        uuid = uuid if isinstance(uuid, str) else uuid.uuid
        transformer = gwr.grid.raw_grid.transformers_2_w.subset(uuid)
        node_uuid = transformer.node_a if side == "hv" else transformer.node_b
        node_uuid = node_uuid.to_list()[0]
        v_rated = gwr.grid.raw_grid.nodes.v_rated.loc[node_uuid]
        node_res = gwr.results.nodes[node_uuid]
        node_side = self._get_node_for_side(side)
        return self.calc_apparent_power(
            node_res, voltage_level_kv=v_rated, node=node_side  # type: ignore
        )

    def active_power(
        self,
        uuid: str | EntityKey,
        gwr: GridWithResults,
        side: Literal["hv", "lv"] = "hv",
    ):
        s = self.apparent_power(uuid, gwr, side)
        return s.apply(lambda x: np.real(x)).rename("p")

    def reactive_power(
        self,
        uuid: str | EntityKey,
        gwr: GridWithResults,
        side: Literal["hv", "lv"] = "hv",
    ):
        s = self.apparent_power(uuid, gwr, side)
        return s.apply(lambda x: np.imag(x)).rename("q")

    def utilisation(
        self,
        uuid: str | EntityKey,
        gwr: GridWithResults,
        side: Literal["hv", "lv"] = "hv",
    ):
        uuid = uuid if isinstance(uuid, str) else uuid.uuid
        transformer = gwr.grid.raw_grid.transformers_2_w.subset(uuid)
        s_rated = transformer.s_rated.to_list()[0]
        return self.apparent_power(uuid, gwr, side).apply(lambda x: np.abs(x)) / s_rated

    def to_complex_power(
        self,
        uuid: str | EntityKey,
        gwr: GridWithResults,
        side: Literal["hv", "lv"] = "hv",
    ):
        p = self.active_power(uuid, gwr, side)
        q = self.reactive_power(uuid, gwr, side)
        data = pd.concat([p, q], axis=1)
        return ComplexPower(data)

    @staticmethod
    def attributes() -> List[str]:
        return ConnectorCurrent.attributes() + ["tap_pos"]

    @staticmethod
    def _get_node_for_side(side) -> Literal["a"] | Literal["b"]:
        if side == "hv":
            return "a"
        elif side == "lv":
            return "b"
        else:
            raise ValueError('Side has to be either "hv" or "lv"')


class Transformers2WResult(
    TimeSeriesDict[K, Transformer2WResult], EntitiesResultDictMixin
):

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return RawGridElementsEnum.TRANSFORMER_2_W
