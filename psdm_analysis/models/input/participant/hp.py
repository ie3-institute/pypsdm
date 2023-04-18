from dataclasses import dataclass

from psdm_analysis.models.input.container.mixins import SpTypeMixin
from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class HeatPumps(SystemParticipants, SpTypeMixin):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.HEATP_PUMP

    @property
    def thermal_bus(self):
        return self.data["thermal_bus"]

    @property
    def p_thermal(self):
        return self.data["p_thermal"]

    @staticmethod
    def entity_attributes() -> [str]:
        return ["thermal_bus"]

    @staticmethod
    def type_attributes() -> [str]:
        return SpTypeMixin.type_attributes() + ["p_thermal"]
