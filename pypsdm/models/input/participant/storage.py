from pandas import Series

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.input.container.mixins import SpTypeMixin
from pypsdm.models.input.participant.participant import SystemParticipantsWithCapacity


class Storages(SpTypeMixin, SystemParticipantsWithCapacity):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.STORAGE

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

    @classmethod
    def entity_attributes(cls) -> list[str]:
        return SystemParticipantsWithCapacity.attributes()

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
