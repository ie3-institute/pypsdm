from dataclasses import dataclass

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import (
    SystemParticipantsWithCapacity,
)


@dataclass(frozen=True)
class ElectricVehicles(SystemParticipantsWithCapacity):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.ELECTRIC_VEHICLE

    @staticmethod
    def capacity_attribute() -> str:
        return "e_storage"

    def s_rated(self):
        return self.data["s_rated"]

    def e_storage(self):
        return self.data["e_storage"]

    def e_cons(self):
        return self.data["e_cons"]

    def ev_type(self):
        return self.data["type_id"]
