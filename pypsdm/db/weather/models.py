import binascii
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from pydantic import ConfigDict
from shapely import Point
from shapely.wkb import loads
from sqlalchemy import Column
from sqlmodel import Field, SQLModel


class WeatherValue(SQLModel, table=True):
    """
    Represents the ICON weather model.
    """

    time: datetime = Field(primary_key=True)
    coordinate_id: Optional[int] = Field(
        primary_key=True, default=None, foreign_key="coordinate.id"
    )
    aswdifd_s: float = Field()
    aswdir_s: float = Field()
    t2m: float = Field()
    u131m: float = Field()
    v131m: float = Field()

    # aliases in SQLModel seem to be broken
    @property
    def diffuse_irradiance(self):
        return self.aswdifd_s

    @property
    def direct_irradiance(self):
        return self.aswdir_s

    @property
    def temperature(self):
        return self.t2m - 273.15

    @property
    def wind_velocity_u(self):
        return self.u131m

    @property
    def wind_velocity_v(self):
        return self.v131m

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
    """Represents a geographical coordinate."""

    # Allow arbitrary types in model configuration
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int = Field(default=None, primary_key=True)

    # Use WKBElement type with the Geography column
    coordinate: WKBElement = Field(
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326, spatial_index=False)
        )
    )

    def __eq__(self, other):
        if isinstance(other, Coordinate):
            return self.coordinate == other.coordinate
        return NotImplemented

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
