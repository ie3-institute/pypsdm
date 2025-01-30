from dataclasses import dataclass

from pandas import Series

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.input.entity import Entities


@dataclass(frozen=True)
class EnergyManagementSystems(Entities):
    @property
    def node(self) -> Series:
        pass

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return SystemParticipantsEnum.ENERGY_MANAGEMENT

    @property
    def control_strategy(self) -> Series:
        return self.data["control_strategy"]

    @property
    def parent_em(self) -> Series:
        return self.data["parent_em"]

    @staticmethod
    def attributes() -> list[str]:
        return Entities.attributes() + [
            "control_strategy",
            "parent_em",
        ]
