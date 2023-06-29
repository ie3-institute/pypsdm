from dataclasses import dataclass

from psdm_analysis.models.input.container.mixins import SpTypeMixin
from psdm_analysis.models.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import (
    SystemParticipantsWithCapacity,
)


@dataclass(frozen=True)
class ElectricVehicles(SystemParticipantsWithCapacity, SpTypeMixin):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.ELECTRIC_VEHICLE

    @staticmethod
    def capacity_attribute() -> str:
        return "e_storage"

    @property
    def e_storage(self):
        return self.data["e_storage"]

    @property
    def e_cons(self):
        return self.data["e_cons"]

    @staticmethod
    def entity_attributes() -> list[str]:
        return []

    @staticmethod
    def type_attributes() -> list[str]:
        return SpTypeMixin.type_attributes() + [
            "e_storage",
            "e_cons",
        ]
