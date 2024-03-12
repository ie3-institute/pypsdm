from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from loguru import logger

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.input.connector.connector import Connector
from pypsdm.models.input.mixins import HasTypeMixin


@dataclass(frozen=True)
class Transformers2W(HasTypeMixin, Connector):
    def __eq__(self, other: object) -> bool:
        return Connector.__eq__(self, other)

    @property
    def type_id(self):
        return self.data["type_id"]

    @property
    def tap_pos(self):
        return self.data["tap_pos"]

    @property
    def auto_tap(self):
        return self.data["auto_tap"]

    @property
    def r_sc(self):
        return self.data["r_sc"]

    @property
    def x_sc(self):
        return self.data["x_sc"]

    @property
    def g_m(self):
        return self.data["g_m"]

    @property
    def b_m(self):
        return self.data["b_m"]

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def v_rated_a(self):
        return self.data["v_rated_a"]

    @property
    def v_rated_b(self):
        return self.data["v_rated_b"]

    @property
    def d_v(self):
        return self.data["d_v"]

    @property
    def d_phi(self):
        return self.data["d_phi"]

    @property
    def tap_side(self):
        """
        True if the tap changer is on the low voltage side, False if it is on the high
        voltage side.
        """
        return self.data["tap_side"]

    @property
    def tap_neutr(self):
        return self.data["tap_neutr"]

    @property
    def tap_min(self):
        return self.data["tap_min"]

    @property
    def tap_max(self):
        return self.data["tap_max"]

    @property
    def tap_ratio(self):
        return 1 + (self.tap_pos - self.tap_neutr) * self.d_v

    @staticmethod
    def _tap_ratio(row):
        return 1 + (row["tap_pos"] - row["tap_neutr"]) * row["d_v"]

    def admittance_matrix(self, uuid_to_idx: dict) -> np.ndarray:
        """TODO: `parallelDevices` not yet considered."""
        if len(self) == 0:
            logger.warning("No trafos. Returning empty array.")
            return np.array([])
        nr_nodes = len(uuid_to_idx)
        Y = np.zeros((nr_nodes, nr_nodes), dtype=complex)
        trafos_data = pd.concat(
            [self.data, self.yij(), self.y0("high"), self.y0("low")], axis=1
        )

        def add_trafo_to_admittance_matrix(
            trafo: pd.Series, Y: np.ndarray, uuid_to_idx: dict
        ):
            i = uuid_to_idx[trafo["node_a"]]
            j = uuid_to_idx[trafo["node_b"]]
            yij = trafo["yij"]
            yaa = trafo["y0_high"]
            ybb = trafo["y0_low"]

            Y[i, i] += yij + yaa
            Y[j, j] += yij + ybb

            Y[i, j] -= yij
            Y[j, i] -= yij

        _ = trafos_data.apply(
            lambda trafo: add_trafo_to_admittance_matrix(trafo, Y, uuid_to_idx), axis=1  # type: ignore
        )
        return Y

    def volt_ratio(self):
        return self.v_rated_a / self.v_rated_b

    def r_sc_lv(self):
        "Resistance with respect to lower voltage side"
        return self.r_sc / (self.volt_ratio() ** 2)

    def x_sc_lv(self):
        "Reactance with respect to lower voltage side"
        return self.x_sc / (self.volt_ratio() ** 2)

    def y0(self, port: Literal["high"] | Literal["low"]):
        """Phase-to-ground admittance"""

        def y0(row):
            tap_side = row["tap_side"]
            if tap_side:
                tap_side = "low"
            else:
                tap_side = "high"
            tap_ratio = self._tap_ratio(row)

            # convert to ohm and relate to low voltage side
            g0 = (row["g_m"] * 1e-9) * ((row["v_rated_a"] / row["v_rated_b"]) ** 2)
            b0 = (row["b_m"] * 1e-9) * ((row["v_rated_a"] / row["v_rated_b"]) ** 2)

            gij = self._gij(row)
            bij = self._bij(row)

            match (port, tap_side):
                case ("high", "high"):
                    gii = 1 / tap_ratio**2 * ((1 - tap_ratio) * gij + g0 / 2)
                    bii = 1 / tap_ratio**2 * ((1 - tap_ratio) * bij + b0 / 2)
                    y0_single = gii + 1j * bii

                case ("high", "low"):
                    gii = (1 - 1 / tap_ratio) * gij + g0 / 2
                    bii = (1 - 1 / tap_ratio) * bij + b0 / 2
                    y0_single = gii + 1j * bii

                case ("low", "high"):
                    gjj = (1 - 1 / tap_ratio) * gij + g0 / 2
                    bjj = (1 - 1 / tap_ratio) * bij + b0 / 2
                    y0_single = gjj + 1j * bjj

                case ("low", "low"):
                    gjj = 1 / tap_ratio**2 * ((1 - tap_ratio) * gij + g0 / 2)
                    bjj = 1 / tap_ratio**2 * ((1 - tap_ratio) * bij + b0 / 2)
                    y0_single = gjj + 1j * bjj

                case _:
                    raise ValueError("Invalid port or tap_side")

            return y0_single

        return (self.data.apply(y0, axis=1)).rename(f"y0_{port}")

    def yij(self):
        """Branch admittance"""
        return ((self.gij() + 1j * self.bij()) / self.tap_ratio).rename("yij")

    def gij(self):
        """Pi equivalent branch conductance"""
        return (self.data.apply(lambda row: self._gij(row), axis=1)).rename("gij")

    @staticmethod
    def _gij(row):
        # relate to low voltage side
        r = row["r_sc"] / ((row["v_rated_a"] / row["v_rated_b"]) ** 2)
        x = row["x_sc"] / ((row["v_rated_a"] / row["v_rated_b"]) ** 2)

        if r == 0:
            return 0
        if x == 0:
            return 1 / r
        else:
            return r / ((r**2) + (x**2))

    def bij(self):
        """Pi equivalent branch susceptance"""
        return (self.data.apply(lambda row: self._bij(row), axis=1)).rename("bij")

    @staticmethod
    def _bij(row):
        r = row["r_sc"] / ((row["v_rated_a"] / row["v_rated_b"]) ** 2)
        x = row["x_sc"] / ((row["v_rated_a"] / row["v_rated_b"]) ** 2)

        if x == 0:
            return 0
        if r == 0:
            return -1 / x
        else:
            return -x / ((r**2) + (x**2))

    def g0(self):
        return ((self.g_m * 1e-9) * self.volt_ratio() ** 2).rename("g0")

    def b0(self):
        return ((self.b_m * 1e-9) * self.volt_ratio() ** 2).rename("b0")

    @staticmethod
    def get_enum() -> RawGridElementsEnum:
        return RawGridElementsEnum.TRANSFORMER_2_W

    @staticmethod
    def entity_attributes() -> list[str]:
        return Connector.attributes() + [
            "tap_pos",
            "auto_tap",
        ]

    @staticmethod
    def type_attributes() -> list[str]:
        return HasTypeMixin.type_attributes() + [
            "r_sc",
            "x_sc",
            "g_m",
            "b_m",
            "s_rated",
            "v_rated_a",
            "v_rated_b",
            "d_v",
            "d_phi",
            "tap_side",
            "tap_neutr",
            "tap_min",
            "tap_max",
        ]
