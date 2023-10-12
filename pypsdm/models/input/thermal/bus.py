from dataclasses import dataclass

from pandas import DataFrame, Series

from pypsdm.models.enums import EntitiesEnum, ThermalGridElementsEnum
from pypsdm.models.input.entity import Entities


@dataclass(frozen=True)
class ThermalBus(Entities):
    data: DataFrame

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return ThermalGridElementsEnum.THERMAL_BUS

    def node(self) -> Series:
        return NotImplemented
