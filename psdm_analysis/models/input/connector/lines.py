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


    @property
    def parallel_devices(self) -> Series:
        return self.data["parallel_devices"]
    @property
    def length(self) -> Series:
        return self.data["length"]

    @property
    def geo_position(self) -> Series:
        return self.data["geo_position"]

    @property
    def olm_characteristic(self) -> Series:
        return self.data["olm_characteristic"]

    @property
    def type(self) -> Series:
        return self.data["type_id"]

    @property
    def v_rated(self) -> Series:
        return self.data["v_rated"]

    @property
    def r(self) -> Series:
        return self.data["r"]

    @property
    def x(self) -> Series:
        return self.data["x"]

    @staticmethod
    def attributes():
        return Entities.attributes() + [
            "node_a",
            "node_b",
            "length",
            "geo_position",
            "olm_characteristic",
            "parallel_devices",
            "type_id",
            "v_rated",
            "r",
            "x"
        ]

    def aggregated_line_length(self) -> float:
        return self.data["length"].sum()

    def relative_line_length(self) -> float:
        return self.data["length"] / len(self.data)

    def find_lines_by_nodes(self, node_uuids):
        return self.data[(self.nodes_a.isin(node_uuids)) | (self.nodes_b.isin(node_uuids))]
