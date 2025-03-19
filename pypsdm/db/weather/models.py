from datetime import datetime
from typing import Optional

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from pydantic import ConfigDict
from shapely.geometry import Point
from shapely.wkb import loads
from sqlalchemy import Column, func
from sqlalchemy.orm import object_session
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

    def _is_valid_wkb_hex(self, hex_str):
        """Check if the string is a valid WKB hex representation."""
        try:
            # Check if it's valid hex first
            if not all(c in "0123456789ABCDEFabcdef" for c in hex_str):
                return False

            # Try to convert hex to bytes and validate as geometry using Shapely
            wkb_bytes = bytes.fromhex(hex_str)
            geom = loads(wkb_bytes)
            return geom.is_valid

        except Exception as e:
            print(f"Invalid WKB: {hex_str}, Error: {e}")
            return False

    @property
    def longitude(self) -> Optional[float]:
        """Extract longitude (x) from the coordinate."""
        if self.coordinate is None:
            return None
        if isinstance(self.coordinate, str) and self.coordinate.startswith("POINT"):
            parts = self.coordinate.replace("POINT(", "").replace(")", "").split()
            return float(parts[0])
        session = object_session(self)
        if session is not None:
            return session.scalar(func.ST_X(self.coordinate))

    @property
    def latitude(self) -> Optional[float]:
        """Extract latitude (y) from the coordinate."""
        if self.coordinate is None:
            return None
        if isinstance(self.coordinate, str) and self.coordinate.startswith("POINT"):
            parts = self.coordinate.replace("POINT(", "").replace(")", "").split()
            return float(parts[1])
        session = object_session(self)
        if session is not None:
            return session.scalar(func.ST_Y(self.coordinate))

    @property
    def y(self) -> float:
        return self.latitude

    @property
    def x(self) -> float:
        return self.longitude

    @property
    def point(self) -> Point:
        """Return Shapely Point object."""
        return Point(self.longitude, self.latitude)

    @staticmethod
    def from_xy(id: int, x: float, y: float) -> "Coordinate":
        """Create a Coordinate object from x (longitude) and y (latitude) values."""
        wkt = f"POINT({x} {y})"
        return Coordinate(id=id, coordinate=wkt)

    @staticmethod
    def from_wkb_hex(id: int, coordinate: str) -> "Coordinate":
        wkb_bytes = bytes.fromhex(coordinate)
        geom = loads(wkb_bytes)
        return Coordinate.from_xy(id=id, x=geom.x, y=geom.y)
