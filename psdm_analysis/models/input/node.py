from dataclasses import dataclass
from typing import List

from pandas import DataFrame

from psdm_analysis.models.input.entity import Entities
from psdm_analysis.models.input.enums import RawGridElementsEnum


@dataclass(frozen=True)
class Nodes(Entities):
    data: DataFrame

    @property
    def geo_position(self):
        return self.data["geo_position"]

    @property
    def longitude(self):
        return self.data["longitude"]

    @property
    def latitude(self):
        return self.data["latitude"]

    @property
    def slack(self):
        return self.data["slack"]

    @property
    def subnet(self):
        return self.data["subnet"]

    @property
    def v_rated(self):
        return self.data["v_rated"]

    @property
    def v_target(self):  # in kV
        return self.data["v_target"]

    @property
    def volt_lvl(self):
        return self.data["volt_lvl"]

    def get_slack_nodes(self):
        return Nodes(self.data[self.slack])

    def node(self):
        return self.data.index

    @staticmethod
    def get_enum() -> RawGridElementsEnum:
        return RawGridElementsEnum.NODE

    @staticmethod
    def attributes() -> List[str]:
        return Entities.attributes() + [
            "v_rated",
            "v_target",
            "slack",
            "geo_position",
            "longitude",
            "latitude",
            "volt_lvl",
            "subnet",
        ]
