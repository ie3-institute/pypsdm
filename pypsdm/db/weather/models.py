from datetime import datetime
from typing import Any, ClassVar, Dict

from geoalchemy2 import Geography, WKBElement
from shapely import Point
from shapely.wkb import loads
from sqlalchemy import Column
from sqlmodel import Field, SQLModel


def ensure_bytes(wkb_element):
    # Get the data from the WKBElement
    data = wkb_element.data
    # Check if it's a memoryview and convert it to bytes if necessary
    if isinstance(data, memoryview):
        return data.tobytes()
    elif isinstance(data, bytes):
        return data
    else:
        raise TypeError("Unexpected data type for WKBElement data")


class WeatherValue(SQLModel, table=True):
    """
    Represents the ICON weather model.
    """

    time: datetime = Field(primary_key=True)
    coordinate_id: int = Field(primary_key=True, foreign_key="coordinate.id")
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

    model_config: ClassVar[Dict[str, Any]] = {"arbitrary_types_allowed": True}

    id: int = Field(default=None, primary_key=True)

    coordinate: Geography = Field(
        sa_column=Column(
            Geography(geometry_type="POINT", srid=4326, spatial_index=False)
        )
    )

    def __init__(self, id: int, coordinate: Geography):
        self.id = id
        self.coordinate = coordinate

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @property
    def point(self) -> Point:
        point_bytes = ensure_bytes(self.coordinate)
        return loads(point_bytes)

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
    def from_xy(id: int, x: float, y: float) -> "Coordinate":
        point = Point(x, y)
        wkb = WKBElement(point.wkb, srid=4326)
        return Coordinate(id, wkb)
