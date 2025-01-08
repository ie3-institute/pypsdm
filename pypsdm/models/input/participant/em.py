from dataclasses import dataclass

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class EnergyManagementSystems(SystemParticipants):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return SystemParticipantsEnum.ENERGY_MANAGEMENT

    @property
    def control_strategy(self):
        return self.data["control_strategy"]


    @staticmethod
    def attributes():
        return SystemParticipants.attributes() + [
            "control_strategy",
        ]
