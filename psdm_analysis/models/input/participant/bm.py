from dataclasses import dataclass
from typing import List

from psdm_analysis.models.input.container.mixins import SpTypeMixin
from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class BiomassPlants(SystemParticipants, SpTypeMixin):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.BIOMASS_PLANT

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
    def active_power_gradient(self):
        return self.data["active_power_gradient"]

    @property
    def eta_conv(self):
        return self.data["eta_conv"]

    @staticmethod
    def entity_attributes() -> List[str]:
        return SystemParticipants.attributes() + [
            "type",
            "market_reaction",
            "cost_controlled",
            "feed_in_tariff",
            "type_id",
            "active_power_gradient",
        ]

    @staticmethod
    def type_attributes() -> [str]:
        return SpTypeMixin.type_attributes() + [
            "active_power_gradient",
            "eta_conv",
        ]
