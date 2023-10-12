from dataclasses import dataclass

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.input.container.mixins import SpTypeMixin
from pypsdm.models.input.participant.participant import SystemParticipantsWithCapacity


@dataclass(frozen=True)
class ElectricVehicles(SpTypeMixin, SystemParticipantsWithCapacity):
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
