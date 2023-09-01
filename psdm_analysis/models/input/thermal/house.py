from dataclasses import dataclass
from typing import List

from pandas import Series

from psdm_analysis.models.enums import EntitiesEnum, ThermalGridElementsEnum
from psdm_analysis.models.input.entity import Entities


@dataclass(frozen=True)
class ThermalHouse(Entities):
    @property
    def eth_losses(self):
        return self.data["eth_losses"]

    @property
    def eth_capa(self):
        return self.data["eth_capa"]

    @property
    def target_temperature(self):
        return self.data["target_temperature"]

    @property
    def upper_temperature_limit(self):
        return self.data["upper_temperature_limit"]

    @property
    def lower_temperature_limit(self):
        return self.data["lower_temperature_limit"]

    @staticmethod
    def attributes() -> List[str]:
        return Entities.attributes() + [
            "thermal_bus",
            "eth_losses",
            "eth_capa",
            "target_temperature",
            "upper_temperature_limit",
            "lower_temperature_limit",
        ]

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return ThermalGridElementsEnum.THERMAL_HOUSE

    def node(self) -> Series:
        return NotImplemented
