from dataclasses import dataclass

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.input.container.mixins import SpTypeMixin
from pypsdm.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class WindEnergyConverters(SpTypeMixin, SystemParticipants):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.WIND_ENERGY_CONVERTER

    @property
    def market_reaction(self):
        return self.data["market_reaction"]

    @property
    def eta_conv(self):
        return self.data["eta_conv"]

    @property
    def rotor_area(self):
        return self.data["rotor_area"]

    @property
    def hub_height(self):
        return self.data["hub_height"]

    @staticmethod
    def entity_attributes() -> list[str]:
        return SystemParticipants.attributes() + ["market_reaction"]

    @staticmethod
    def type_attributes() -> list[str]:
        return SpTypeMixin.type_attributes() + [
            "cp_characteristic",
            "eta_conv",
            "rotor_area",
            "hub_height",
        ]
