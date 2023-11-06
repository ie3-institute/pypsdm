from dataclasses import dataclass

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.input.participant.mixins import SpTypeMixin
from pypsdm.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class BiomassPlants(SpTypeMixin, SystemParticipants):
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
    def entity_attributes() -> list[str]:
        return SystemParticipants.attributes() + [
            "market_reaction",
            "cost_controlled",
            "feed_in_tariff",
        ]

    @staticmethod
    def type_attributes() -> list[str]:
        return SpTypeMixin.type_attributes() + [
            "active_power_gradient",
            "eta_conv",
        ]
