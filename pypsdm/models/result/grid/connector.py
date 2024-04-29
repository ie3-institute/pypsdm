from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal

import numpy as np
import pandas as pd
from pandas import DataFrame, Series

from pypsdm.models.ts.base import K, TimeSeries, TimeSeriesDict
from pypsdm.models.ts.types import ComplexCurrent, ComplexVoltage


@dataclass
class ConnectorCurrent(TimeSeries):

    def __init__(self, data: DataFrame, end: datetime | None = None):
        super().__init__(data, end)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def __add__(self, other):
        raise NotImplementedError("Adding connector results is not defined")

    @property
    def i_a(self) -> ComplexCurrent:
        data = self.data[["i_a_mag", "i_a_ang"]].rename(
            columns={"i_a_mag": "i_mag", "i_a_ang": "i_ang"}
        )
        return ComplexCurrent(data)

    @property
    def i_a_mag(self) -> Series:
        """
        Port a current magnitude in Ampere.
        """
        return self.data["i_a_mag"]

    @property
    def i_a_ang(self) -> Series:
        """
        Port a current magnitude in Ampere.
        """
        return self.data["i_a_ang"]

    @property
    def i_a_complex(self) -> Series:
        return self.i_a_mag * np.exp(1j * np.radians(self.i_a_ang))

    @property
    def i_b(self) -> ComplexCurrent:
        data = self.data[["i_b_mag", "i_b_ang"]].rename(
            columns={"i_b_mag": "i_mag", "i_b_ang": "i_ang"}
        )
        return ComplexCurrent(data)

    @property
    def i_b_ang(self) -> Series:
        """
        Port b current angle in degrees.
        """
        return self.data["i_b_ang"]

    @property
    def i_b_mag(self) -> Series:
        """
        Port b current magnitude in Ampere.
        """
        return self.data["i_b_mag"]

    @property
    def i_b_complex(self) -> Series:
        return self.i_b_mag * np.exp(1j * np.radians(self.i_b_ang))

    def calc_apparent_power(
        self, node_res: ComplexVoltage, voltage_level_kv: float, node="a"
    ):  # in kVA
        def s_rated_fn(i_complex):
            return (
                math.sqrt(3)
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

    def utilisation(
        self, i_max: int | float, side: Literal["a", "b"] = "a"
    ) -> pd.Series:
        if side == "a":
            i = self.i_a_complex
        elif side == "b":
            i = self.i_b_complex
        else:
            raise ValueError(f"Invalid side: {side}. Should be 'a' or 'b'.")
        return i.abs() / i_max

    @staticmethod
    def attributes() -> List[str]:
        return ["i_a_ang", "i_a_mag", "i_b_ang", "i_b_mag"]


class ConnectorCurrentDict(TimeSeriesDict[K, ConnectorCurrent]):

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def i_a_ang(self, ffill: bool = True, favor_ids: bool = True) -> DataFrame:
        return self.attr_df("i_a_ang", ffill=ffill, favor_ids=favor_ids)

    def i_a_mag(self, ffill: bool = True, favor_ids: bool = True) -> DataFrame:
        return self.attr_df("i_a_mag", ffill=ffill, favor_ids=favor_ids)

    def i_b_ang(self, ffill: bool = True, favor_ids: bool = True) -> DataFrame:
        return self.attr_df("i_b_ang", ffill=ffill, favor_ids=favor_ids)

    def i_b_mag(self, ffill: bool = True, favor_ids: bool = True) -> DataFrame:
        return self.attr_df("i_b_mag", ffill=ffill, favor_ids=favor_ids)
