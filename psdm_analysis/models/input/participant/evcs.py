from dataclasses import dataclass

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class EvChargingStations(SystemParticipants):
    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "EvChargingStations":
        return cls._from_csv(
            path, delimiter, SystemParticipantsEnum.EV_CHARGING_STATION
        )

    @property
    def charging_points(self):
        return self.data["charging_points"]

    @property
    def location_types(self):
        return self.data["location_type"]

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def electric_current_type(self):
        return self.data["electric_current_type"]

    def get_public_evcs(self):
        return self.data[self.location_types.isin(["CUSTOMER_PARKING", "WORK"])]

    def get_home_evcs(self):
        return self.data[self.location_types.isin(["HOME"])]
