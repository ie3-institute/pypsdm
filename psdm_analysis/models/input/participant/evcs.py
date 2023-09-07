from dataclasses import dataclass
from enum import Enum
from string import Template

from psdm_analysis.models.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class EvChargingStations(SystemParticipants):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.EV_CHARGING_STATION

    @property
    def charging_points(self):
        return self.data["charging_points"]

    @property
    def location_type(self):
        return self.data["location_type"]

    @property
    def electric_current_type(self):
        return self.data["type"]

    @property
    def v2g_support(self):
        return self.data["v2g_support"]

    @property
    def cos_phi_rated(self):
        return self.data["cos_phi_rated"]

    def get_public_evcs(self):
        return self.data[
            self.location_type.isin(
                [EvcsLocationType.CUSTOMER_PARKING.value, EvcsLocationType.WORK.value]
            )
        ]

    def get_home_evcs(self):
        return self.data[self.location_type.isin([EvcsLocationType.HOME.value])]

    @staticmethod
    def attributes() -> list[str]:
        return SystemParticipants.attributes() + [
            "charging_points",
            "location_type",
            "type",
            "v2g_support",
            "cos_phi_rated",
        ]


class EvcsLocationType(Enum):
    HOME = "HOME"
    WORK = "WORK"
    CUSTOMER_PARKING = "CUSTOMER_PARKING"
    STREET = "STREET"
    CHARGING_HUB_TOWN = "CHARGING_HUB_TOWN"
    CHARGING_HUB_HIGHWAY = "CHARGING_HUB_HIGHWAY"


evcs_type = Template("$id($s_rated|$current_type)")
