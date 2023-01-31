import json
from dataclasses import dataclass
from typing import List

from pandas import DataFrame

from psdm_analysis.io.utils import read_csv
from psdm_analysis.models.entity import Entities


@dataclass(frozen=True)
class Nodes(Entities):
    data: DataFrame

    @staticmethod
    def attributes() -> List[str]:
        return super().attributes() + [
            "v_target",
            "slack",
            "geo_position",
            "volt_lvl",
            "subnet",
        ]

    def geo_position(self):
        return self.data["geo_position"]

    def longitude(self):
        return self.data["longitude"]

    def latitude(self):
        return self.data["latitude"]

    @classmethod
    def from_csv(cls, path: str, delimiter: str):
        data = read_csv(path, "node_input.csv", delimiter)
        # todo: deal with nans
        data["longitude"] = data["geo_position"].apply(
            lambda geo_json: json.loads(geo_json)["coordinates"][0]
        )
        data["latitude"] = data["geo_position"].apply(
            lambda geo_json: json.loads(geo_json)["coordinates"][1]
        )
        return Nodes(data.set_index("uuid"))
