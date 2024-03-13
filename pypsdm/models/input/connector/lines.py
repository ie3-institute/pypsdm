from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd
from loguru import logger
from pandas import Series

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.input.connector.connector import Connector
from pypsdm.models.input.mixins import HasTypeMixin


@dataclass(frozen=True)
class Lines(HasTypeMixin, Connector):
    def __eq__(self, other: object) -> bool:
        return Connector.__eq__(self, other)

    @property
    def length(self) -> Series:
        """Line length in km."""
        return self.data["length"]

    @property
    def geo_position(self) -> Series:
        return self.data["geo_position"]

    @property
    def olm_characteristic(self) -> Series:
        """
        Characteristic of possible overhead line monitoring Can be given in the
        form of olm:{<List of Pairs>}. The pairs are wind velocity in x and
        permissible loading in y.
        """
        return self.data["olm_characteristic"]

    @property
    def v_rated(self) -> Series:
        """Rated voltage in kV"""
        return self.data["v_rated"]

    @property
    def r(self) -> Series:
        """Phase resistance per length in ohm/km."""
        return self.data["r"]

    @property
    def x(self) -> Series:
        """Phase reactance per length in ohm/km."""
        return self.data["x"]

    @property
    def g(self) -> Series:
        """Phase conductance per length in uS/km."""
        return self.data["g"]

    @property
    def b(self) -> Series:
        """Phase susceptance per length in uS/km."""
        return self.data["b"]

    @property
    def i_max(self) -> Series:
        """Maximum permissible current in A."""
        return self.data["i_max"]

    def gij(self) -> Series:
        """Pi equivalent circuit: Branch conductance."""

        def gij(row: Series):
            r = row["r"] * row["length"]
            x = row["x"] * row["length"]

            if r == 0:
                return 0
            if x == 0:
                return 1 / r
            else:
                return r / ((r**2) + (x**2))

        return (self.data.apply(lambda row: gij(row), axis=1)).rename("gij")  # type: ignore

    def bij(self) -> Series:
        """Pi equivalent circuit: Branch susceptance."""

        def bij(row: Series):
            r = row["r"] * row["length"]
            x = row["x"] * row["length"]

            if x == 0:
                return 0
            if r == 0:
                return -1 / x
            else:
                return -x / ((r**2) + (x**2))

        return (self.data.apply(lambda row: bij(row), axis=1)).rename("bij")  # type: ignore

    def yij(self) -> Series:
        """Pi equivalent circuit: Branch admittance."""
        return (self.gij() + 1j * self.bij()).rename("yij").astype(complex)

    def y0(self) -> Series:
        """Pi equivalent circuit: Ground admittance."""
        return (self.g0() + 1j * self.b0()).rename("y0").astype(complex)

    def b0(self) -> Series:
        """Pi quivalent circuit: Phase to ground susceptance."""
        return (self.b * 1e-6 * self.length / 2).rename("b0")

    def g0(self) -> Series:
        """Pi quivalent circuit: Phase to ground conductance."""
        return (self.g * 1e-6 * self.length / 2).rename("g0")

    def admittance_matrix(self, uuid_to_idx: dict) -> np.ndarray:
        """TODO: `parallelDevices` not yet considered."""
        if len(self) == 0:
            logger.warning("No lines. Returning empty array.")
            return np.array([])
        nr_nodes = len(uuid_to_idx)
        Y = np.zeros((nr_nodes, nr_nodes), dtype=complex)
        lines_data = pd.concat([self.data, self.yij(), self.y0()], axis=1)

        def add_line_to_admittance_matrix(
            line: pd.Series, Y: np.ndarray, uuid_to_idx: dict
        ):
            i = uuid_to_idx[line["node_a"]]
            j = uuid_to_idx[line["node_b"]]
            yij = line["yij"]
            yaa = line["y0"]

            Y[i, i] += yij + yaa
            Y[j, j] += yij + yaa

            Y[i, j] -= yij
            Y[j, i] -= yij

        _ = lines_data.apply(
            lambda line: add_line_to_admittance_matrix(line, Y, uuid_to_idx), axis=1  # type: ignore
        )
        return Y

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
        return Connector.attributes() + [
            "length",
            "geo_position",
            "olm_characteristic",
        ]

    @staticmethod
    def type_attributes() -> List[str]:
        return HasTypeMixin.type_attributes() + ["r", "x", "b", "g", "i_max", "v_rated"]
