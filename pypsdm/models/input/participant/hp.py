from dataclasses import dataclass

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.input.container.mixins import SpTypeMixin
from pypsdm.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class HeatPumps(SpTypeMixin, SystemParticipants):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.HEAT_PUMP

    @property
    def thermal_bus(self):
        return self.data["thermal_bus"]

    @property
    def p_thermal(self):
        return self.data["p_thermal"]

    @staticmethod
    def entity_attributes() -> list[str]:
        return SystemParticipants.attributes() + ["thermal_bus"]

    @staticmethod
    def type_attributes() -> list[str]:
        return SpTypeMixin.type_attributes() + ["p_thermal"]
