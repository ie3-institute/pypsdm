import json
from dataclasses import dataclass
from typing import List

from pandas import DataFrame

from psdm_analysis.io.utils import read_csv
from psdm_analysis.models.entity import Entities


@dataclass(frozen=True)
class Nodes(Entities):
    data: DataFrame

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

    @staticmethod
    def attributes() -> List[str]:
        return super().attributes() + [
            "v_target",
            "slack",
            "geo_position",
            "volt_lvl",
            "subnet",
        ]

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
    def volt_lvl(self):
        return self.data["volt_lvl"]

    def get_slack_nodes(self):
        return Nodes(self.data[self.slack])