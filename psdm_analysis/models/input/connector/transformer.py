from dataclasses import dataclass

from psdm_analysis.models.input.connector.connector import Connector
from psdm_analysis.models.input.container.mixins import HasTypeMixin
from psdm_analysis.models.input.enums import RawGridElementsEnum


@dataclass(frozen=True)
class Transformers2W(Connector, HasTypeMixin):
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

    @staticmethod
    def entity_attributes() -> list[str]:
        return [
            "node_a",
            "node_b",
            "parallel_devices",
            "type_id",
            "tap_pos",
            "auto_tap",
        ]

    @staticmethod
    def type_attributes() -> list[str]:
        return [
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

    @staticmethod
    def get_enum() -> RawGridElementsEnum:
        return RawGridElementsEnum.TRANSFORMER_2_W
