import binascii
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry, WKBElement
from shapely import Point
from shapely.geometry.base import BaseGeometry
from shapely.wkb import loads
from shapely.wkb import dumps
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
    id: int = Field(default=None, primary_key=True)

    # Use Geometry for storing WKB data (binary format)
    coordinate: bytes = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326))
    )

    def __init__(self, id: int, coordinate: bytes):
        self.id = id
        self.coordinate = coordinate

    def __eq__(self, other):
        return self.id == other.id if isinstance(other, Coordinate) else NotImplemented

    def __hash__(self):
        return hash(self.id)

    @property
    def point(self) -> BaseGeometry:
        if isinstance(self.coordinate, WKBElement):
            wkb_str = str(self.coordinate)
            coordinate = bytes.fromhex(wkb_str)
        else:
            coordinate = self.coordinate
        return loads(coordinate)


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
    def from_xy(id: int, x: float, y: float) -> 'Coordinate':
        point = Point(x, y)
        wkb_data = dumps(point)
        return Coordinate(id=id, coordinate=wkb_data)

    @staticmethod
    def from_hex(id: int, wkb_hex: str) -> 'Coordinate':
        bytes = binascii.unhexlify(wkb_hex)
        return Coordinate(id=id, coordinate=bytes)