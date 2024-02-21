from dataclasses import dataclass
from typing import List

from pypsdm.models.enums import EntitiesEnum, RawGridElementsEnum
from pypsdm.models.input.connector.connector import Connector


@dataclass(frozen=True)
class Switches(Connector):

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @property
    def closed(self):
        return self.data["closed"]

    def get_closed(self) -> "Switches":
        return self.subset(self.data.query("closed == True").index.tolist())

    def get_opened(self) -> "Switches":
        return self.subset(self.data.query("closed == False").index.tolist())

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
