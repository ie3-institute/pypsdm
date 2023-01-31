from dataclasses import dataclass

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import (
    SystemParticipantsWithCapacity,
)


@dataclass(frozen=True)
class ElectricVehicles(SystemParticipantsWithCapacity):
    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "ElectricVehicles":
        return cls._from_csv(path, delimiter, SystemParticipantsEnum.ELECTRIC_VEHICLE)

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
