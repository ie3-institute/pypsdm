from dataclasses import dataclass
from typing import List

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.models.entity import ResultEntities
from psdm_analysis.models.result.participant.dict import ResultDict


@dataclass(frozen=True)
class Transformer2WResult(ResultEntities):
    @staticmethod
    def attributes() -> List[str]:
        return ["i_a_ang", "i_a_mag", "i_b_ang", "i_b_mag", "tap_pos"]

    @property
    def i_a_ang(self) -> Series:
        return self.data["i_a_ang"]

    @property
    def i_a_mag(self) -> Series:
        return self.data["i_a_mag"]

    @property
    def i_b_ang(self) -> Series:
        return self.data["i_b_ang"]

    @property
    def i_b_mag(self) -> Series:
        return self.data["i_b_mag"]

    @property
    def tap_pos(self) -> Series:
        return self.data["tap_pos"]


@dataclass(frozen=True)
class Transformers2WResult(ResultDict):
    entities: dict[str, Transformer2WResult]

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
