from dataclasses import dataclass

from pandas import DataFrame

from psdm_analysis.models.input.connector.connector import Connector
from psdm_analysis.models.input.enums import EntitiesEnum, RawGridElementsEnum


@dataclass(frozen=True)
class Switches(Connector):
    data: DataFrame

    @staticmethod
    def attributes() -> list[str]:
        return Connector.attributes() + ["closed"]

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return RawGridElementsEnum.SWITCH

    @property
    def closed(self):
        return self.data["closed"]

    def get_closed(self) -> "Switches":
        return self.subset(self.data.query("closed == True").index)

    def get_opened(self) -> "Switches":
        return self.subset(self.data.query("closed == False").index)
