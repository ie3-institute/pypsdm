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

    time: Optional[datetime] = Field(primary_key=True)
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
    def wind_velicty_u(self):
        return self.u131m

    @property
    def wind_velicty_v(self):
        return self.v131m


class Coordinate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    coordinate: str = Field()

    @property
    def point(self) -> Point:
        wkb_str = self.coordinate
        wkb_bytes = binascii.unhexlify(wkb_str)
        return loads(wkb_bytes)

    @property
    def latitude(self) -> float:
        return self.point.y

    @property
    def longitude(self) -> float:
        return self.point.x
