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
    def connected_assets(self):
        return self.data["connected_assets"]

    @property
    def control_strategy(self):
        return self.data["control_strategy"]

    def uuid_to_connected_assets(self):
        return self.connected_assets.to_dict()

    @staticmethod
    def attributes():
        return SystemParticipants.attributes() + [
            "connected_assets",
            "control_strategy",
        ]
