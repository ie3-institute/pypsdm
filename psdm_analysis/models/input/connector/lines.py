from dataclasses import dataclass
from typing import List

from pandas import Series

from psdm_analysis.models.enums import RawGridElementsEnum
from psdm_analysis.models.input.connector.connector import Connector
from psdm_analysis.models.input.container.mixins import HasTypeMixin


@dataclass(frozen=True)
class Lines(HasTypeMixin, Connector):
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

    def aggregated_line_length(self) -> float:
        """
        Returns the aggregated length of all lines.

        Returns:
            float: Aggregated length of all lines.
        """
        return self.data["length"].sum()

    def relative_line_length(self) -> Series:
        """
        Returns the relative length of all lines.

        Returns:
            float: Relative length of all lines.
        """
        return self.length / len(self.data)

    @staticmethod
    def get_enum() -> RawGridElementsEnum:
        return RawGridElementsEnum.LINE

    @staticmethod
    def entity_attributes() -> List[str]:
        return [
            "length",
            "geo_position",
            "olm_characteristic",
        ]

    @staticmethod
    def type_attributes() -> List[str]:
        return HasTypeMixin.type_attributes() + ["r", "x", "b", "g", "i_max", "v_rated"]
