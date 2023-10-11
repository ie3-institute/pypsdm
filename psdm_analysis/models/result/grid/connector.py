from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.models.result.entity import ResultEntities
from psdm_analysis.models.result.grid.node import NodeResult
from psdm_analysis.models.result.participant.dict import ResultDict


@dataclass(frozen=True)
class ConnectorResult(ResultEntities):
    def __add__(self, other):
        raise NotImplementedError("Adding connector results is not defined")

    @property
    def i_a_ang(self) -> Series:
        return self.data["i_a_ang"]

    @property
    def i_a_mag(self) -> Series:
        return self.data["i_a_mag"]

    @property
    def i_a_complex(self) -> Series:
        return self.i_a_mag * np.exp(1j * np.radians(self.i_a_ang))

    @property
    def i_b_ang(self) -> Series:
        return self.data["i_b_ang"]

    @property
    def i_b_mag(self) -> Series:
        return self.data["i_b_mag"]

    @property
    def i_b_complex(self) -> Series:
        return self.i_b_mag * np.exp(1j * np.radians(self.i_b_ang))

    def calc_apparent_power(
        self, node_res: NodeResult, voltage_level_kv: float, node="a"
    ):  # in kVA
        s_rated_fn = (
            lambda i_complex: math.sqrt(3)
            * node_res.v_complex(voltage_level_kv)  # type: ignore
            * np.conj(i_complex)
        )
        if node == "a":
            res = s_rated_fn(self.i_a_complex)
        elif node == "b":
            res = s_rated_fn(self.i_b_complex)
        else:
            raise ValueError("Node must be either hv or lv")
        return res

    @staticmethod
    def attributes() -> List[str]:
        return ["i_a_ang", "i_a_mag", "i_b_ang", "i_b_mag"]


@dataclass(frozen=True)
class ConnectorsResult(ResultDict):
    entities: dict[str, ConnectorResult]

    @property
    def i_a_ang(self) -> DataFrame:
        return pd.concat(
            [
                node_res.i_a_ang.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        )

    @property
    def i_a_mag(self) -> DataFrame:
        return pd.concat(
            [
                node_res.i_a_mag.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        )

    @property
    def i_b_ang(self) -> DataFrame:
        return pd.concat(
            [
                node_res.i_b_ang.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        )

    @property
    def i_b_mag(self) -> DataFrame:
        return pd.concat(
            [
                node_res.i_b_mag.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        )
