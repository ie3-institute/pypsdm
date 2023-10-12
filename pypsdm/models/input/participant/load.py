from dataclasses import dataclass
from typing import List

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class Loads(SystemParticipants):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.LOAD

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def standard_load_profile(self):
        return self.data["load_profile"]

    @property
    def dsm(self):
        return self.data["dsm"]

    @property
    def e_cons_annual(self):
        return self.data["e_cons_annual"]

    @property
    def cos_phi_rated(self):
        return self.data["cos_phi_rated"]

    @staticmethod
    def attributes() -> List[str]:
        return SystemParticipants.attributes() + [
            "load_profile",
            "dsm",
            "e_cons_annual",
            "s_rated",
            "cos_phi_rated",
        ]
