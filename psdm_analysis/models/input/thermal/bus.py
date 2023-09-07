from dataclasses import dataclass

from pandas import DataFrame, Series

from psdm_analysis.models.enums import EntitiesEnum, ThermalGridElementsEnum
from psdm_analysis.models.input.entity import Entities


@dataclass(frozen=True)
class ThermalBus(Entities):
    data: DataFrame

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return ThermalGridElementsEnum.THERMAL_BUS

    def node(self) -> Series:
        return NotImplemented
