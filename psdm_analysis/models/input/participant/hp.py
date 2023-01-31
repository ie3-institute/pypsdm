from dataclasses import dataclass

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class HeatPumps(SystemParticipants):
    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "HeatPumps":
        return cls._from_csv(path, delimiter, SystemParticipantsEnum.HEATP_PUMP)

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def cos_phi_rated(self):
        return self.data["cos_phi_rated"]

    @property
    def p_thermal(self):
        return self.data["p_thermal"]

    @property
    def thermal_bus(self):
        return self.data["thermal_bus"]
