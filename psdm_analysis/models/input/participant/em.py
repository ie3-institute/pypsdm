from dataclasses import dataclass

from psdm_analysis.models.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class EnergyManagementSystems(SystemParticipants):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.ENERGY_MANAGEMENT

    @property
    def connected_assets(self):
        return self.data["connected_assets"]

    @property
    def control_strategy(self):
        return self.data["control_strategy"]

    def uuid_to_connected_assets(self):
        return self.connected_assets.to_dict()
