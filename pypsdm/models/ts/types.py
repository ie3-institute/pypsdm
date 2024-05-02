from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING, List, Self, Sequence, Union

from pandas import DataFrame

from pypsdm.models.ts.base import K, TimeSeries, TimeSeriesDict
from pypsdm.models.ts.mixins import (
    ComplexCurrentMixin,
    ComplexPowerDictMixin,
    ComplexPowerMixin,
    ComplexVoltageDictMixin,
    ComplexVoltageMixin,
    SocDictMixin,
    SocMixin,
    WeatherDataDictMixin,
    WeatherDataMixin,
)
from pypsdm.processing.dataframe import add_df
from pypsdm.processing.series import Tuple, add_series

if TYPE_CHECKING:
    from pypsdm.db.weather.models import WeatherValue


class ComplexPower(TimeSeries, ComplexPowerMixin):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def __add__(self, other: Self) -> "ComplexPower":
        if isinstance(other, ComplexPower):
            self_data = self.data[ComplexPower.attributes()]
            other_data = other.data[ComplexPower.attributes()]
            data = add_df(self_data, other_data)
            return ComplexPower(data)
        else:
            raise ValueError(
                f"Addition with type {type(other)} not or not yet supported"
            )

    def __sub__(self, other: Self):
        return self + (other * -1)

    def __mul__(self, other: Union[float, int]):
        if isinstance(other, float) or isinstance(other, int):
            updated_data = self.data * other
            return ComplexPower(updated_data)
        else:
            raise ValueError(
                f"Multiplication with type {type(other)} not or not yet supported"
            )

    # commutative multiplication (a*b=b*a)
    __rmul__ = __mul__

    @classmethod
    def sum(cls, results: Sequence[Self]) -> "ComplexPower":
        if len(results) == 0:
            return cls.empty()
        if len(results) == 1:
            return results[0]
        return reduce(lambda a, b: a + b, results)

    @staticmethod
    def attributes() -> List[str]:
        return ["p", "q"]


class ComplexPowerDict(TimeSeriesDict[K, ComplexPower], ComplexPowerDictMixin):
    def sum(self) -> ComplexPower:
        return ComplexPower.sum(list(self.values()))

    def load_and_generation(self) -> Tuple[float, float]:
        return self.sum().load_and_generation_energy()


@ComplexPower.register
class ComplexPowerWithSoc(TimeSeries, ComplexPowerMixin, SocMixin):
    def as_complex_power(self) -> ComplexPower:
        return ComplexPower(self.data.drop(columns=["soc"]))

    def add_with_soc(
        self, this_capacity: float, other: "ComplexPowerWithSoc", other_capacity: float
    ) -> Self:
        data = add_df(self.data.drop(columns=["soc"]), other.data.drop(columns=["soc"]))
        total_capacity = this_capacity + other_capacity
        soc = add_series(
            self.soc * this_capacity / total_capacity,
            other.soc * other_capacity / total_capacity,
            "soc",
        )
        data["soc"] = soc
        return self.__class__(
            data,
        )

    @staticmethod
    def sum_with_soc(
        results: list[Tuple[float, "ComplexPowerWithSoc"]],
    ) -> "ComplexPowerWithSoc":
        if len(results) == 0:
            return ComplexPowerWithSoc.empty()
        if len(results) == 1:
            return results[0][1]
        this_capacity, agg = results[0]
        for other_capacity, result in results[1::]:
            agg = agg.add_with_soc(this_capacity, result, other_capacity)
        return agg

    @staticmethod
    def attributes() -> List[str]:
        return ["p", "q", "soc"]


@ComplexPowerDict.register
class ComplexPowerWithSocDict(
    TimeSeriesDict[K, ComplexPowerWithSoc], ComplexPowerDictMixin, SocDictMixin
):
    def sum(self) -> ComplexPower:
        return ComplexPower.sum([v.as_complex_power() for v in self.values()])

    def sum_with_soc(self, capacities: dict[K, float]) -> ComplexPowerWithSoc:
        if not self:
            return ComplexPowerWithSoc.empty()
        capacity_participant = []
        for key, res in self.items():
            capacity = capacities[key]
            capacity_participant.append((capacity, res))
        return ComplexPowerWithSoc.sum_with_soc(capacity_participant)


class ComplexCurrent(TimeSeries, ComplexCurrentMixin):
    @staticmethod
    def attributes() -> list[str]:
        return ["i_mag", "i_ang"]


class ComplexCurrentDict(TimeSeriesDict[K, ComplexCurrent]):
    pass


class ComplexVoltage(TimeSeries, ComplexVoltageMixin):
    @staticmethod
    def attributes() -> list[str]:
        return ["v_mag", "v_ang"]


class ComplexVoltageDict(TimeSeriesDict[K, ComplexVoltage], ComplexVoltageDictMixin):
    pass


@ComplexVoltage.register
class ComplexVoltagePower(ComplexVoltage, ComplexPower):
    def __init__(self, data):
        super().__init__(data)

    def __add__(self, other: Self):
        raise NotImplementedError

    def __eq__(self, other: object):
        return super().__eq__(other)

    def as_complex_voltage(self):
        return ComplexVoltage(self.data[ComplexVoltage.attributes()])

    def as_complex_power(self):
        return ComplexPower(self.data[ComplexPower.attributes()])


@ComplexVoltageDict.register
class ComplexVoltagePowerDict(
    TimeSeriesDict[K, ComplexVoltagePower],
    ComplexVoltageDictMixin,
    ComplexPowerDictMixin,
):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def complex_power_sum(self) -> ComplexPower:
        return ComplexPower.sum(list(self.values()))


class CoordinateWeather(TimeSeries, WeatherDataMixin):

    def __add__(self, other) -> Self:
        return self.__class__(add_df(self.data, other.data))

    def __mul__(self, other: float | int) -> Self:
        return self.__class__(self.data * other)

    __rmul__ = __mul__

    @classmethod
    def from_value_list(cls, values: list[WeatherValue]):
        df = cls.df_from_value_list(values)
        if df["coordinate_id"].nunique() > 1:
            raise ValueError("Multiple coordinate ids in weather data")
        df.drop(columns=["coordinate_id"], inplace=True)
        return cls(df)

    @staticmethod
    def df_from_value_list(values: list[WeatherValue]):
        from pypsdm.db.weather.models import WeatherValue

        value_dicts = [value.model_dump() for value in values]
        df = DataFrame(value_dicts, columns=WeatherValue.__table__.columns.keys())
        df.rename(columns=WeatherValue.name_mapping(), inplace=True)
        df.set_index("time", inplace=True, drop=True)
        return df

    @staticmethod
    def attributes() -> List[str]:
        return [
            "diffuse_irradiance",
            "direct_irradiance",
            "temperature",
            "wind_velocity_u",
            "wind_velocity_v",
        ]


class WeatherDict(TimeSeriesDict[int, CoordinateWeather], WeatherDataDictMixin):

    @classmethod
    def from_value_list(cls, values: list[WeatherValue]):
        df = CoordinateWeather.df_from_value_list(values)
        grps = df.groupby("coordinate_id")
        dct = {}
        for coord_id, grp in grps:
            grp = grp.drop(columns=["coordinate_id"])
            dct[coord_id] = CoordinateWeather(grp)
        return cls(dct)
