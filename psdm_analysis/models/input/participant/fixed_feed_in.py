from dataclasses import dataclass

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


@dataclass(frozen=True)
class FixedFeedIns(SystemParticipants):
    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "FixedFeedIns":
        return cls._from_csv(path, delimiter, SystemParticipantsEnum.FIXED_FEED_IN)

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def cos_phi_rated(self):
        return self.data["cos_phi_rated"]
