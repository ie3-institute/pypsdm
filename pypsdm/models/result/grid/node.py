from dataclasses import dataclass
from datetime import datetime
from numbers import Real
from typing import List, Optional, Type

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.input.entity import Entities
from pypsdm.models.input.node import Nodes
from pypsdm.models.result.entity import ResultEntities
from pypsdm.models.result.participant.dict import ResultDict, ResultDictType


@dataclass(frozen=True)
class NodeResult(ResultEntities):
    def __eq__(self, other) -> bool:
        return super().__eq__(other)

    def __add__(self, _):
        return NotImplemented

    @property
    def v_mag(self) -> Series:  # in Ampere
        return self.data["v_mag"]

    @property
    def v_ang(self) -> Series:
        return self.data["v_ang"]

    def v_complex(self, v_rated_kv_src: Real | Nodes | None = None) -> Series:
        if isinstance(v_rated_kv_src, Nodes):
            v_rated_kv = v_rated_kv_src.subset(self.input_model).v_rated.iloc[0]
        elif isinstance(v_rated_kv_src, Real):
            v_rated_kv = v_rated_kv_src
        elif v_rated_kv_src is None:
            v_rated_kv = 1
        else:
            raise ValueError(
                f"Received unexpected type for v_rated: {type(v_rated_kv_src)}"
            )

        return (self.v_mag * v_rated_kv) * np.exp(1j * np.radians(self.v_ang))

    @staticmethod
    def attributes() -> List[str]:
        return ["v_ang", "v_mag"]

    # todo: fix me
    @staticmethod
    def build_from_nominal_data(
        uuid: str,
        name: Optional[str],
        data: DataFrame,
        rated_voltage: float,
    ) -> "NodeResult":
        data["v_mag"] = data["v_mag"].divide(rated_voltage)
        return NodeResult(RawGridElementsEnum.NODE, uuid, name, data)


@dataclass(frozen=True)
class NodesResult(ResultDict):
    entities: dict[str, NodeResult]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def from_csv(
        cls: Type[ResultDictType],
        simulation_data_path: str,
        delimiter: str | None = None,
        simulation_end: Optional[datetime] = None,
        input_entities: Optional[Entities] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ) -> ResultDictType:
        return super().from_csv(
            RawGridElementsEnum.NODE,
            simulation_data_path,
            delimiter,
            simulation_end,
            input_entities,
            filter_start,
            filter_end,
        )

    def v_mag(self) -> DataFrame:
        if not self.entities:
            return pd.DataFrame()
        return pd.concat(
            [
                node_res.v_mag.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        )

    def v_ang(self) -> DataFrame:
        if not self.entities:
            return pd.DataFrame()
        return pd.concat(
            [
                node_res.v_ang.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        )

    def v_complex(self, nodes: Nodes | None = None) -> DataFrame:
        if not self.entities:
            return pd.DataFrame().astype(complex)
        return pd.concat(
            [
                node_res.v_complex(nodes).rename(node_res.input_model).rename(uuid)
                for uuid, node_res in self.entities.items()
            ],
            axis=1,
        )  # type: ignore

    def v_mag_describe(self) -> DataFrame:
        return self._describe(self.v_mag)

    def v_ang_describe(self) -> DataFrame:
        return self._describe(self.v_ang)

    @staticmethod
    def _describe(data: DataFrame):
        return data.describe().transpose()

    @classmethod
    def create_empty(cls, entity_type=RawGridElementsEnum.NODE) -> "NodesResult":
        return super().create_empty(entity_type)
