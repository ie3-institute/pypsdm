from dataclasses import dataclass

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class EnergyManagementSystems(SystemParticipants):
    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "EnergyManagementSystems":
        return cls._from_csv(path, delimiter, SystemParticipantsEnum.ENERGY_MANAGEMENT)

    @property
    def connected_assets(self):
        return self.data["connected_assets"]

    @property
    def control_strategy(self):
        return self.data["control_strategy"]

    def uuid_to_connected_assets(self):
        return self.connected_assets.to_dict()
