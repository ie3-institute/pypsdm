from pandas import Series

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import (
    SystemParticipantsWithCapacity,
)


class Storages(SystemParticipantsWithCapacity):
    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "Storages":
        return cls._from_csv(path, delimiter, SystemParticipantsEnum.STORAGE)

    @property
    def type(self) -> Series:
        return self.data["type"]

    @property
    def behaviour(self) -> Series:
        return self.data["behaviour"]

    @staticmethod
    def capacity_attribute() -> str:
        return "e_storage"

    # in kVA
    @property
    def s_rated(self) -> Series:
        return self.data["s_rated"]

    @property
    def cos_phi_rated(self) -> Series:
        return self.data["cos_phi_rated"]

    @property
    def p_max(self) -> Series:
        return self.data["p_max"]

    @property
    def eta(self) -> Series:
        return self.data["eta"]

    @property
    def dod(self) -> Series:
        return self.data["dod"]

    @property
    def life_time(self) -> Series:
        return self.data["life_time"]

    @property
    def life_cycle(self) -> Series:
        return self.data["life_cycle"]
