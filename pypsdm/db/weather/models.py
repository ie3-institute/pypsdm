import binascii
from datetime import datetime
from typing import Optional

from shapely import Point
from shapely.wkb import loads
from sqlmodel import Field, SQLModel


class WeatherValue(SQLModel, table=True):
    """
    Represents the ICON weather model.
    """

    time: datetime = Field(default=None, primary_key=True)
    coordinate_id: Optional[int] = Field(
        primary_key=True, default=None, foreign_key="coordinate.id"
    )
    dif_irradiance: float = Field(alias="aswdifd_s")
    dir_irradiance: float = Field(alias="aswdir_s")
    temp: float = Field(alias="t2m")
    wind_u: float = Field(alias="u131m")
    wind_v: float = Field(alias="v131m")

    @property
    def diffuse_irradiance(self):
        return self.dif_irradiance

    @property
    def direct_irradiance(self):
        return self.dir_irradiance

    @property
    def temperature(self):
        return self.temp - 273.15

    @property
    def wind_velocity_u(self):
        return self.wind_u

    @property
    def wind_velocity_v(self):
        return self.wind_v

    @staticmethod
    def name_mapping():
        return {
            "time": "time",
            "coordinate_id": "coordinate_id",
            "aswdifd_s": "diffuse_irradiance",
            "aswdir_s": "direct_irradiance",
            "t2m": "temperature",
            "u131m": "wind_velocity_u",
            "v131m": "wind_velocity_v",
        }


class Coordinate(SQLModel, table=True):
    id: int = Field(primary_key=True)
    coordinate: str = Field()

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @property
    def point(self) -> Point:
        wkb_str = self.coordinate
        wkb_bytes = binascii.unhexlify(wkb_str)
        return loads(wkb_bytes)

    @property
    def latitude(self) -> float:
        return self.point.y

    @property
    def y(self) -> float:
        return self.point.y

    @property
    def longitude(self) -> float:
        return self.point.x

    @property
    def x(self) -> float:
        return self.point.x

    @staticmethod
    def from_xy(id, x, y):
        wkb = Point(x, y).wkb_hex
        return Coordinate(id=id, coordinate=wkb)
