from dataclasses import dataclass
from typing import List

from pandas import DataFrame, Series

from psdm_analysis.models.input.connector.connector import Connector
from psdm_analysis.models.input.container.mixins import HasTypeMixin
from psdm_analysis.models.input.enums import RawGridElementsEnum


@dataclass(frozen=True)
class Lines(Connector, HasTypeMixin):
    data: DataFrame

    @staticmethod
    def get_enum() -> RawGridElementsEnum:
        return RawGridElementsEnum.LINE

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
    def v_rated(self) -> Series:
        return self.data["v_rated"]

    @property
    def r(self) -> Series:
        return self.data["r"]

    @property
    def x(self) -> Series:
        return self.data["x"]

    @property
    def b(self) -> Series:
        return self.data["b"]

    @property
    def i_max(self) -> Series:
        return self.data["i_max"]

    @staticmethod
    def entity_attributes() -> List[str]:
        return [
            "node_a",
            "node_b",
            "length",
            "geo_position",
            "olm_characteristic",
            "parallel_devices",
        ]

    @staticmethod
    def type_attributes() -> List[str]:
        return HasTypeMixin.attributes() + ["r", "x", "b", "i_max", "v_rated"]

    def aggregated_line_length(self) -> float:
        return self.data["length"].sum()

    def relative_line_length(self) -> float:
        return self.data["length"] / len(self.data)

    def find_lines_by_nodes(self, node_uuids):
        return self.data[
            (self.node_a.isin(node_uuids)) | (self.node_b.isin(node_uuids))
        ]
