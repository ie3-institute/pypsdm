from dataclasses import dataclass

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class FixedFeedIns(SystemParticipants):
    @staticmethod
    def get_enum() -> SystemParticipantsEnum:
        return SystemParticipantsEnum.FIXED_FEED_IN

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def cos_phi_rated(self):
        return self.data["cos_phi_rated"]
