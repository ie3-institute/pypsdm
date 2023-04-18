from dataclasses import dataclass

from pandas import DataFrame

from psdm_analysis.models.entity import Entities
from psdm_analysis.models.input.enums import EntitiesEnum, RawGridElementsEnum


@dataclass(frozen=True)
class Switches(Entities):
    data: DataFrame

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return RawGridElementsEnum.SWITCH

    @property
    def node_a(self):
        return self.data["node_a"]

    @property
    def node_b(self):
        return self.data["node_b"]

    @property
    def closed(self):
        return self.data["closed"]
