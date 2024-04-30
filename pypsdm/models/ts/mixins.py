from abc import ABC
from numbers import Real
from typing import Tuple

import numpy as np
from pandas import DataFrame, Series

from pypsdm.models.ts.base import TimeSeriesDictMixin
from pypsdm.processing.dataframe import divide_positive_negative
from pypsdm.processing.series import (
    duration_weighted_sum,
    hourly_mean_resample,
    pos_and_neg_area,
)


class AttributeMixin(ABC):
    pass


class ActivePowerMixin(AttributeMixin):
    @property
    def p(self):
        return self.data["p"]  # type: ignore

    def energy(self) -> float:
        return duration_weighted_sum(self.p)

    def load_and_generation_energy(self) -> Tuple[float, float]:
        return pos_and_neg_area(self.p)

    def divide_load_generation(self) -> Tuple[DataFrame, DataFrame]:
        return divide_positive_negative(self.data)  # type: ignore

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


class ActivePowerDictMixin(TimeSeriesDictMixin):

    def p(
        self,
        ffill=True,
        favor_ids: bool = True,
    ) -> DataFrame:
        return self.attr_df("p", ffill, favor_ids)

    def p_sum(self, ffill=True) -> Series:
        if not self.data:  # type: ignore
            return Series(dtype=float)
        return self.p(ffill).sum(axis=1).rename("p_sum")

    def energy(self) -> float:
        sum = 0
        for participant in self.values():  # type: ignore
            sum += participant.energy()
        return sum


class ReactivePowerMixin(AttributeMixin):
    @property
    def q(self):
        return self.data["q"]  # type: ignore

    def reactive_energy(self) -> float:
        return duration_weighted_sum(self.q)


class ReactivePowerDictMixin(TimeSeriesDictMixin):

    def q(
        self,
        ffill=True,
        favor_ids: bool = True,
    ) -> DataFrame:
        return self.attr_df("q", ffill, favor_ids)

    def q_sum(self, ffill=True):
        if not self.data:  # type: ignore
            return Series(dtype=float)
        return self.q(ffill).sum(axis=1).rename("q_sum")


class ComplexPowerMixin(ActivePowerMixin, ReactivePowerMixin):
    def complex_power(self) -> Series:
        return self.p + 1j * self.q

    def angle(self):
        return self.complex_power().apply(lambda x: np.angle(x, deg=True))


class ComplexPowerDictMixin(ActivePowerDictMixin, ReactivePowerDictMixin):

    def complex_power(self, ffill=True, favor_ids=True) -> DataFrame:
        return self.p(ffill, favor_ids) + 1j * self.q(ffill, favor_ids)


class SocMixin(AttributeMixin):
    @property
    def soc(self):
        return self.data["soc"]  # type: ignore


class SocDictMixin(TimeSeriesDictMixin):

    def soc(self, ffill=True, favor_ids=True) -> DataFrame:
        return self.attr_df("soc", ffill, favor_ids)


class CurrentAngleMixin(AttributeMixin):

    @property
    def i_ang(self):
        return self.data["i_ang"]  # type: ignore


class CurrentAngleDictMixin(TimeSeriesDictMixin):

    def i_ang(self, ffill: bool = True, favor_ids: bool = True) -> DataFrame:
        return self.attr_df("i_ang", ffill, favor_ids)


class CurrentMagnitudeMixin(AttributeMixin):

    @property
    def i_mag(self):
        return self.data["i_mag"]  # type: ignore


class CurrentMagnitudeDictMixin(TimeSeriesDictMixin):

    def i_mag(self, ffill: bool = True, favor_ids: bool = True) -> DataFrame:
        return self.attr_df("i_mag", ffill, favor_ids)


class ComplexCurrentMixin(CurrentMagnitudeMixin, CurrentAngleMixin):

    def i_complex(self) -> Series:
        return self.i_mag * np.exp(1j * np.radians(self.i_ang))


class ComplexCurrentDictMixin(CurrentMagnitudeDictMixin, CurrentAngleDictMixin):

    def i_complex(self, favor_ids: bool = True) -> DataFrame:
        return self.attr_df("i_complex", False, favor_ids)


class VoltageMagnitudeMixin(AttributeMixin):
    @property
    def v_mag(self):
        return self.data["v_mag"]  # type: ignore


class VoltageAngleMixin(AttributeMixin):
    @property
    def v_ang(self):
        return self.data["v_ang"]  # type: ignore


class VoltageMagnitudeDictMixin(TimeSeriesDictMixin):
    def v_mag(self, ffill: bool = True, favor_ids: bool = True) -> DataFrame:
        return self.attr_df("v_mag", ffill, favor_ids)


class VoltageAngleDictMixin(TimeSeriesDictMixin):
    def v_ang(self, ffill: bool = True, favor_ids: bool = True) -> DataFrame:
        return self.attr_df("v_ang", ffill, favor_ids)


class ComplexVoltageMixin(VoltageMagnitudeMixin, VoltageAngleMixin):
    def v_complex(self, v_rated_kv_src: Real | None = None) -> Series:
        if isinstance(v_rated_kv_src, Real):
            v_rated_kv = v_rated_kv_src
        elif v_rated_kv_src is None:
            v_rated_kv = 1
        else:
            raise ValueError(
                f"Received unexpected type for v_rated: {type(v_rated_kv_src)}"
            )

        return (self.v_mag * v_rated_kv) * np.exp(1j * np.radians(self.v_ang))


class ComplexVoltageDictMixin(VoltageMagnitudeDictMixin, VoltageAngleDictMixin):
    def v_complex(
        self, v_rated: float | None = None, favor_ids: bool = True
    ) -> DataFrame:
        # ffill not supported for complex numbers
        return self.attr_df("v_complex", False, favor_ids, v_rated)
