from dataclasses import dataclass
from typing import List

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class WindEnergyConverters(SystemParticipants):
    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "WindEnergyConverters":
        return cls._from_csv(
            path, delimiter, SystemParticipantsEnum.WIND_ENERGY_CONVERTER
        )

    @property
    def type(self):
        return self.data["type"]

    @property
    def type_id(self):
        return self.data["type_id"]

    @property
    def market_reaction(self):
        return self.data["market_reaction"]

    @property
    def cost_controlled(self):
        return self.data["cost_controlled"]

    @property
    def feed_in_tariff(self):
        return self.data["feed_in_tariff"]

    @property
    def capex(self):
        return self.data["capex"]

    @property
    def opex(self):
        return self.data["opex"]

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def cos_phi_rated(self):
        return self.data["cos_phi_rated"]

    @property
    def eta_conv(self):
        return self.data["eta_conv"]

    @property
    def rotor_area(self):
        return self.data["active_power_gradient"]

    @property
    def hub_height(self):
        return self.data["hub_height"]

    @staticmethod
    def attributes() -> List[str]:
        return SystemParticipants.attributes() + [
            "type",
            "type_id" "market_reaction",
            "cost_controlled",
            "feed_in_tariff",
            "capex",
            "opex",
            "s_rated",
            "cos_phi_rated",
            "eta_conv",
            "rotor_area",
            "hub_height",
        ]
