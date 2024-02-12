from dataclasses import dataclass
from typing import List

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class PhotovoltaicPowerPlants(SystemParticipants):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT

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
    def eta_conv(self):
        return self.data["eta_conv"]

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
            "s_rated",
            "albedo",
            "azimuth",
            "elevation_angle",
            "eta_conv",
            "k_g",
            "k_t",
            "market_reaction",
            "cos_phi_rated",
        ]
