from dataclasses import dataclass

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.input.participant.participant import SystemParticipants


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

    def to_csv(self, path: str, mkdirs=True, delimiter: str = ","):
        self.data["connected_assets"] = self.connected_assets.apply(
            lambda x: f"{' '.join(x)}"
        )
        return super().to_csv(path, mkdirs, delimiter)

    @staticmethod
    def attributes():
        return SystemParticipants.attributes() + [
            "connected_assets",
            "control_strategy",
        ]
