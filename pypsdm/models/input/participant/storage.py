from pandas import Series

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.input.participant.mixins import SpTypeMixin
from pypsdm.models.input.participant.participant import SystemParticipantsWithCapacity


class Storages(SpTypeMixin, SystemParticipantsWithCapacity):
    def __eq__(self, other: object) -> bool:
        return SystemParticipantsWithCapacity.__eq__(self, other)

    @staticmethod
    def get_enum() -> EntitiesEnum:
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
    def eta_charging(self) -> Series:
        return self.data["eta_charging"]

    @property
    def eta_discharging(self) -> Series:
        return self.data["eta_discharging"]

    @classmethod
    def entity_attributes(cls) -> list[str]:
        return SystemParticipantsWithCapacity.attributes()

    @staticmethod
    def type_attributes() -> list[str]:
        return SpTypeMixin.type_attributes() + [
            "p_max",
            "active_power_gradient",
            "e_storage",
            "eta_charging",
            "eta_discharging",
        ]
