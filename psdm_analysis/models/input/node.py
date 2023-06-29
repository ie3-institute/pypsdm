import os
from dataclasses import dataclass
from typing import List

from pandas import DataFrame

from psdm_analysis.io.utils import df_to_csv
from psdm_analysis.models.input.entity import Entities
from psdm_analysis.models.enums import RawGridElementsEnum


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

    @property
    def node(self):
        return self.data.index

    def get_slack_nodes(self):
        return Nodes(self.data[self.slack])

    def to_csv(self, path: str, mkdirs=True, delimiter: str = ","):
        # filter columns latitude and longitude as they are not part of the original data model
        data = self.data.drop(columns=["latitude", "longitude"])
        if mkdirs:
            os.makedirs(os.path.normpath(path), exist_ok=True)
        df_to_csv(data, path, self.get_enum().get_csv_input_file_name(), delimiter)

    @staticmethod
    def get_enum() -> RawGridElementsEnum:
        return RawGridElementsEnum.NODE

    @classmethod
    def attributes(cls, include_additional: bool = True) -> List[str]:
        return Entities.attributes() + [
            "v_rated",
            "v_target",
            "slack",
            "geo_position",
            "volt_lvl",
            "subnet",
        ]
