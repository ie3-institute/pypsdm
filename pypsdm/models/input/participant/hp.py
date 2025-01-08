from dataclasses import dataclass

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.input.participant.mixins import SpTypeMixin
from pypsdm.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class HeatPumps(SpTypeMixin, SystemParticipants):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return SystemParticipantsEnum.HEAT_PUMP

    @property
    def thermal_bus(self):
        return self.data["thermal_bus"]

    @property
    def p_thermal(self):
        return self.data["p_thermal"]

    @property
    def em(self):
        return self.data["em"]

    @staticmethod
    def entity_attributes() -> list[str]:
        return SystemParticipants.attributes() + ["thermal_bus"]

    @staticmethod
    def type_attributes() -> list[str]:
        return SpTypeMixin.type_attributes() + ["p_thermal"]
