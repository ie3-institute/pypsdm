from dataclasses import dataclass
from typing import List

from psdm_analysis.models.enums import EntitiesEnum, RawGridElementsEnum
from psdm_analysis.models.input.connector.connector import Connector


@dataclass(frozen=True)
class Switches(Connector):
    @property
    def closed(self):
        return self.data["closed"]

    def get_closed(self) -> "Switches":
        return self.subset(self.data.query("closed == True").index)

    def get_opened(self) -> "Switches":
        return self.subset(self.data.query("closed == False").index)

    @staticmethod
    def attributes() -> list[str]:
        # ignore parallel devices since this is always 1
        # also we cannot read the attribute in the PSDM at the moment
        return [
            attr
            for attr in Connector.attributes() + ["closed"]
            if attr != "parallel_devices"
        ]

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return RawGridElementsEnum.SWITCH

    @staticmethod
    def bool_attributes() -> List[str]:
        return Connector.bool_attributes() + ["closed"]
