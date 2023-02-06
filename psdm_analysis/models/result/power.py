import dataclasses
import os
import re
from dataclasses import dataclass
from typing import List, Union

import pandas as pd
from pandas import Series

from psdm_analysis.io.utils import get_absolute_path
from psdm_analysis.models.entity import ResultEntities
from psdm_analysis.models.input.enums import EntitiesEnum, SystemParticipantsEnum
from psdm_analysis.processing.dataframe import divide_positive_negative
from psdm_analysis.processing.series import (
    add_series,
    duration_weighted_sum,
    hourly_mean_resample,
    load_and_generation,
)


@dataclass(frozen=True)
class PQResult(ResultEntities):
    def __add__(self, other: "PQResult"):
        p_sum = add_series(self.p, other.p, "p")
        q_sum = add_series(self.q, other.q, "q")
        summed_data = p_sum.to_frame().join(q_sum)
        return PQResult(
            self.type
            if self.type == other.type
            else SystemParticipantsEnum.PARTICIPANTS_SUM,
            "PQResult - Sum",
            "PQResult - Sum",
            summed_data,
        )

    def __sub__(self, other: "PQResult"):
        return self + (other * -1)

    def __mul__(self, other: Union[float, int]):
        if isinstance(other, float) or isinstance(other, int):
            updated_data = self.data * other
            return PQResult(self.type, self.name, self.input_model, updated_data)
        else:
            raise ValueError(
                f"Multiplication with type {type(other)} not or not yet supported"
            )

    # commutative multiplication (a*b=b*a)
    __rmul__ = __mul__

    def __eq__(self, other):
        if not isinstance(other, PQResult):
            return False
        return (self.data == other.data).all()

    @classmethod
    def from_csv(cls, file_path: str, sp_type: EntitiesEnum, name: str = None):
        file_path = get_absolute_path(file_path)
        data = pd.read_csv(file_path)
        data["time"] = pd.to_datetime(data["time"])
        data = data.set_index("time", drop=True)
        file_name = os.path.basename(file_path)
        is_default_file_name = re.match(
            f"{sp_type.get_csv_result_file_name()}_.*", file_name
        )
        input_model = file_name.split("_")[-1] if is_default_file_name else file_name
        return cls(sp_type, name if name else input_model, input_model, data)

    def to_csv(self, path: str, file_name: str = None, delimiter: str = ","):
        file_name = file_name if file_name else self.get_default_output_name()
        self.data.to_csv(os.path.join(path, file_name), sep=delimiter)

    def get_default_output_name(self):
        return self.input_model + "_" + self.type.get_csv_result_file_name()

    @property
    def p(self):
        return self.data["p"]

    @property
    def q(self):
        return self.data["q"]

    @staticmethod
    def attributes() -> List[str]:
        return ["p", "q"]

    @classmethod
    # todo: find a way for parallel calculation
    def sum(cls, results: List["PQResult"]) -> "PQResult":
        if len(results) == 0:
            return PQResult.create_empty(
                SystemParticipantsEnum.PARTICIPANTS_SUM, "", ""
            )
        if len(results) == 1:
            return results[0]
        agg = results[0]
        for result in results[1::]:
            agg += result
        return agg

    def energy(self) -> float:
        return duration_weighted_sum(self.p)

    def load_and_generation(self) -> (float, float):
        return load_and_generation(self.p)

    def divide_load_generation(self):
        load, generation = divide_positive_negative(self.data)
        return dataclasses.replace(self, data=load), dataclasses.replace(
            self, data=generation
        )

    def daily_usage(self, device_power_mw):
        return (
            self.p()
            .groupby(self.p.index.date)
            .apply(lambda series: duration_weighted_sum(series.abs()))
            / device_power_mw
        )

    def annual_duration_series(self, drop_index=True):
        return (
            hourly_mean_resample(self.p)
            .sort_values(ascending=False)
            .reset_index(drop=drop_index)
        )

    def hourly_resample(self):
        updated_data = self.data.apply(lambda col: hourly_mean_resample(col), axis=0)
        return PQResult(self.type, self.name, self.input_model, updated_data)


@dataclass(frozen=True)
class PQWithSocResult(PQResult):
    def add_with_soc(
        self, this_capacity: float, other: "PQWithSocResult", other_capacity: float
    ):
        p_sum = add_series(self.p, other.p, "p")
        q_sum = add_series(self.q, other.q, "q")
        total_capacity = this_capacity + other_capacity
        soc = add_series(
            self.soc() * this_capacity / total_capacity,
            other.soc() * other_capacity / total_capacity,
            "soc",
        )
        summed_data = p_sum.to_frame().join([q_sum, soc])
        return PQWithSocResult(
            self.type,
            "PQResult - Sum",
            "PQResult - Sum",
            summed_data,
        )

    @staticmethod
    # todo: find a way for parallel calculation
    def sum_with_soc(results: [(float, "PQWithSocResult")]) -> "PQWithSocResult":
        if len(results) == 0:
            return PQWithSocResult.create_empty(
                SystemParticipantsEnum.PARTICIPANTS_SUM, "", ""
            )
        if len(results) == 1:
            return results[0][1]
        this_capacity, agg = results[0]
        for other_capacity, result in results[1::]:
            agg = agg.add_with_soc(this_capacity, result, other_capacity)
        return agg

    def soc(self) -> Series:
        return self.data["soc"]

    @staticmethod
    def attributes() -> List[str]:
        return ["p", "q", "capacity"]
