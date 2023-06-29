from pandas import Series

from psdm_analysis.models.input.container.mixins import SpTypeMixin
from psdm_analysis.models.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import (
    SystemParticipantsWithCapacity,
)


class Storages(SystemParticipantsWithCapacity, SpTypeMixin):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.STORAGE

    @property
    def behaviour(self) -> Series:
        return self.data["behaviour"]

    @staticmethod
    def capacity_attribute() -> str:
        return "e_storage"

    @property
    def p_max(self) -> Series:
        return self.data["p_max"]

    @property
    def active_power_gradient(self) -> Series:
        return self.data["active_power_gradient"]

    @property
    def eta(self) -> Series:
        return self.data["eta"]

    @property
    def dod(self) -> Series:
        return self.data["dod"]

    @property
    def life_time(self) -> Series:
        return self.data["life_time"]

    @property
    def life_cycle(self) -> Series:
        return self.data["life_cycle"]

    @staticmethod
    def entity_attributes() -> list[str]:
        return [
            "behaviour",
        ]

    @staticmethod
    def type_attributes() -> list[str]:
        return SpTypeMixin.type_attributes() + [
            "p_max",
            "active_power_gradient",
            "e_storage",
            "eta",
            "dod",
            "life_time",
            "life_cycle",
        ]
