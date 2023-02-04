from dataclasses import dataclass
from typing import List

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class Loads(SystemParticipants):
    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "Loads":
        return cls._from_csv(path, delimiter, SystemParticipantsEnum.LOAD)

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def standard_load_profile(self):
        return self.data["standard_load_profile"]

    @property
    def e_cons_annual(self):
        return self.data["e_cons_annual"]

    @property
    def cosphi_rated(self):
        return self.data["cosphi_rated"]

    @staticmethod
    def attributes() -> List[str]:
        return SystemParticipants.attributes() + [
            "standard_load_profile",
            "e_cons_annual",
            "s_rated",
            "cosphi_rated",
        ]
