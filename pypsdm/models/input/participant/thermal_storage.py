from pandas import Series

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.input.participant.participant import SystemParticipants


class ThermalStorages(SystemParticipants):
    def __eq__(self, other: object) -> bool:
        return SystemParticipants.__eq__(self, other)

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return SystemParticipantsEnum.THERMAL_STORAGE

    @property
    def thermal_bus(self) -> Series:
        return self.data["thermal_bus"]

    @property
    def storage_volume_lvl(self) -> Series:
        return self.data["storage_volume_lvl"]

    @property
    def inlet_temp(self) -> Series:
        return self.data["inlet_temp"]

    @property
    def return_temp(self) -> Series:
        return self.data["return_temp"]

    """specific heat capacity"""
    @property
    def c(self) -> Series:
        return self.data["c"]

    @property
    def p_thermal_max(self) -> Series:
        return self.data["p_thermal_max"]

    @classmethod
    def entity_attributes(cls) -> list[str]:
        return SystemParticipants.attributes() + [
            "thermal_bus",
            "storage_volume_lvl",
            "inlet_temp",
            "return_temp",
            "c",
            "p_thermal_max",
        ]