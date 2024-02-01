import dataclasses
import os
import re
from dataclasses import dataclass
from functools import reduce
from pathlib import Path
from typing import List, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from pandas import Series

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.result.entity import ResultEntities
from pypsdm.processing.dataframe import divide_positive_negative
from pypsdm.processing.series import (
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
            (
                self.entity_type
                if self.entity_type == other.entity_type
                else SystemParticipantsEnum.PARTICIPANTS_SUM
            ),
            "PQResult - Sum",
            "PQResult - Sum",
            summed_data,
        )

    def __sub__(self, other: "PQResult"):
        return self + (other * -1)

    def __mul__(self, other: Union[float, int]):
        if isinstance(other, float) or isinstance(other, int):
            updated_data = self.data * other
            return PQResult(self.entity_type, self.input_model, self.name, updated_data)
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

    @property
    def p(self):
        return self.data["p"]

    @property
    def q(self):
        return self.data["q"]

    def complex_power(self):
        return self.p + 1j * self.q

    def angle(self):
        return self.complex_power().apply(lambda x: np.angle(x, deg=True))

    def energy(self) -> float:
        return duration_weighted_sum(self.p)

    def load_and_generation(self) -> Tuple[float, float]:
        return load_and_generation(self.p)

    def divide_load_generation(self):
        load, generation = divide_positive_negative(self.data)
        return dataclasses.replace(self, data=load), dataclasses.replace(
            self, data=generation
        )

    def full_load_hours(self, device_power_kw, period="Y"):
        """
        Calculates the full load hours for the given period.

        Args:
            device_power_mw: The power of the device in MW
            period: The period to calculate the full load hours for. Default is year.
                    Use to_period() aliases, like Y for year, M for month, D for day, etc.
                    (https://pandas.pydata.org/docs/user_guide/timeseries.html#timeseries-period-aliases)

        Returns:
            A series with the full load hours within the determined periods.
        """
        return self.p.groupby(self.p.index.to_period(period)).apply(
            lambda series: duration_weighted_sum(series.abs())
        ) / (
            device_power_kw / 1000
        )  # convert to MW since results are in MW

    def annual_duration_series(self, drop_index=True):
        return (
            hourly_mean_resample(self.p)
            .sort_values(ascending=False)
            .reset_index(drop=drop_index)  # type: ignore
        )

    def hourly_resample(self):
        updated_data = self.data.apply(lambda col: hourly_mean_resample(col), axis=0)
        return PQResult(self.entity_type, self.input_model, self.name, updated_data)

    def to_csv(self, path: str, file_name: str | None = None, delimiter: str = ","):
        if not isinstance(path, str):
            path = str(path)
        file_name = file_name if file_name else self.get_default_output_name()
        self.data.to_csv(
            os.path.join(path, file_name), sep=delimiter, index_label="time"
        )

    def get_default_output_name(self) -> str:
        return self.input_model + "_" + self.entity_type.get_csv_result_file_name()

    @classmethod
    def from_csv(
        cls, file_path: str | Path, sp_type: EntitiesEnum, name: str | None = None
    ):
        file_path = Path(file_path).resolve()
        data = pd.read_csv(file_path)
        data["time"] = pd.to_datetime(data["time"])
        data = data.set_index("time", drop=True)
        file_name = os.path.basename(file_path)
        is_default_file_name = re.match(
            f"{sp_type.get_csv_result_file_name()}_.*", file_name
        )
        input_model = file_name.split("_")[-1] if is_default_file_name else file_name
        return cls(sp_type, name if name else input_model, input_model, data)

    @classmethod
    # todo: find a way for parallel calculation
    def sum(cls, results: Sequence["PQResult"]) -> "PQResult":
        if len(results) == 0:
            return PQResult.create_empty(
                SystemParticipantsEnum.PARTICIPANTS_SUM, "", ""
            )
        if len(results) == 1:
            return results[0]
        return reduce(lambda a, b: a + b, results)

    @staticmethod
    def attributes() -> List[str]:
        return ["p", "q"]


@dataclass(frozen=True)
class PQWithSocResult(PQResult):
    def add_with_soc(
        self, this_capacity: float, other: "PQWithSocResult", other_capacity: float
    ):
        p_sum = add_series(self.p, other.p, "p")
        q_sum = add_series(self.q, other.q, "q")
        total_capacity = this_capacity + other_capacity
        soc = add_series(
            self.soc * this_capacity / total_capacity,
            other.soc * other_capacity / total_capacity,
            "soc",
        )
        summed_data = p_sum.to_frame().join([q_sum, soc])
        return PQWithSocResult(
            self.entity_type,
            "PQResult - Sum",
            "PQResult - Sum",
            summed_data,
        )

    @staticmethod
    # todo: find a way for parallel calculation
    def sum_with_soc(
        results: list[Tuple[float, "PQWithSocResult"]]
    ) -> "PQWithSocResult":
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

    @property
    def soc(self) -> Series:
        return self.data["soc"]

    @staticmethod
    def attributes() -> List[str]:
        return ["p", "q", "capacity"]
