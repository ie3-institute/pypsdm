from dataclasses import dataclass
from typing import List

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class PhotovoltaicPowerPlants(SystemParticipants):
    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "PhotovoltaicPowerPlants":
        return cls._from_csv(
            path, delimiter, SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT
        )

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def albedo(self):
        return self.data["albedo"]

    @property
    def azimuth(self):
        return self.data["azimuth"]

    @property
    def elevation_angle(self):
        return self.data["elevation_angle"]

    @property
    def k_g(self):
        return self.data["k_g"]

    @property
    def k_t(self):
        return self.data["k_t"]

    @property
    def market_reaction(self):
        return self.data["market_reaction"]

    @property
    def cos_phi_rated(self):
        return self.data["cos_phi_rated"]

    @staticmethod
    def attributes() -> List[str]:
        return SystemParticipants.attributes() + [
            "albedo",
            "azimuth",
            "elevation_angle",
            "k_g",
            "k_t",
            "market_reaction",
            "cos_phi_rated",
        ]
