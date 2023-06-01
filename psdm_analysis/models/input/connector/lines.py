from dataclasses import dataclass
from typing import List

from pandas import Series

from psdm_analysis.models.input.connector.connector import Connector
from psdm_analysis.models.input.container.mixins import HasTypeMixin
from psdm_analysis.models.input.enums import RawGridElementsEnum


@dataclass(frozen=True)
class Lines(Connector, HasTypeMixin):
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

    def aggregated_line_length(self) -> float:
        """
        Returns the aggregated length of all lines.

        Returns:
            float: Aggregated length of all lines.
        """
        return self.data["length"].sum()

    def relative_line_length(self) -> float:
        """
        Returns the relative length of all lines.

        Returns:
            float: Relative length of all lines.
        """
        return self.data["length"] / len(self.data)

    def find_lines_by_nodes(self, node_uuids: list[str]) -> "Lines":
        """
        Returns all lines that are connected to any of the given nodes.

        Args:
            node_uuids: List of node uuids to find lines for.

        Returns:
            Lines: Lines that are connected to any of the given nodes.
        """
        return Lines(
            self.data[(self.node_a.isin(node_uuids)) | (self.node_b.isin(node_uuids))]
        )

    def find_line_by_node_pair(self, node_a_uuid: str, node_b_uuid: str) -> "Lines":
        """
        Returns the line that connects the given nodes.

        Args:
            node_a_uuid (str): UUID of the first node.
            node_b_uuid (str): UUID of the second node.

        Returns:
            Lines: Line that connects the given nodes. Will be empty if no line is found.
        """

        return Lines(
            self.data[
                ((self.node_a == node_a_uuid) & (self.node_b == node_b_uuid))
                | ((self.node_a == node_b_uuid) & (self.node_b == node_a_uuid))
            ]
        )

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
