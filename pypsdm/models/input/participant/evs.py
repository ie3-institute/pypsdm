from dataclasses import dataclass

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.input.participant.mixins import SpTypeMixin
from pypsdm.models.input.participant.participant import SystemParticipantsWithCapacity


@dataclass(frozen=True)
class ElectricVehicles(SpTypeMixin, SystemParticipantsWithCapacity):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return SystemParticipantsEnum.ELECTRIC_VEHICLE

    @staticmethod
    def capacity_attribute() -> str:
        return "e_storage"

    @property
    def s_rated_dc(self):
        return self.data["s_rated_dc"]

    @property
    def s_rated_ac(self):
        return self.data["s_rated_ac"]

    @property
    def e_storage(self):
        return self.data["e_storage"]

    @property
    def e_cons(self):
        return self.data["e_cons"]

    @staticmethod
    def entity_attributes() -> list[str]:
        return SystemParticipantsWithCapacity.attributes()

    @staticmethod
    def type_attributes() -> list[str]:
        return SpTypeMixin.type_attributes() + [
            "s_rated_dc",
            "s_rated_ac",
            "e_storage",
            "e_cons",
        ]
