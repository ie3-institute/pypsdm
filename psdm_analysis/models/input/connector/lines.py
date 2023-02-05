from dataclasses import dataclass

from pandas import DataFrame, Series

from psdm_analysis.models.entity import Entities
from psdm_analysis.models.input.enums import RawGridElementsEnum


@dataclass(frozen=True)
class Lines(Entities):
    data: DataFrame

    @classmethod
    def from_csv(cls, path: str, delimiter: str):
        return cls._from_csv(path, delimiter, RawGridElementsEnum.LINE)

    @property
    def nodes_a(self) -> Series:
        return self.data["node_a"]

    @property
    def nodes_b(self) -> Series:
        return self.data["node_b"]

    @staticmethod
    def attributes():
        return Entities.attributes() + [
            "node_a",
            "node_b",
            "parallel_devices",
            "type",
            "length",
            "geo_position",
            "olm_characteristic",
        ]

    def aggregated_line_length(self) -> float:
        return self.data["length"].sum()

    def relative_line_length(self) -> float:
        return self.data["length"] / len(self.data)
