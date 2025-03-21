from datetime import datetime

import pytest
from sqlalchemy import select, text

from pypsdm.db.weather.models import Coordinate, WeatherValue


@pytest.mark.docker_required
def test_create_coordinate(db_session):
    """Test creating a coordinate."""
    coordinates = []
    coord_1 = Coordinate.from_xy(1, 8.645, 50.123)
    coord_2 = Coordinate.from_xy(2, 7.46, 51.5)
    coordinates: list[Coordinate] = coordinates + [coord_1, coord_2]

    query = text(
        """
        INSERT INTO coordinate (id, coordinate)
        VALUES (:id, ST_SetSRID(ST_GeomFromWKB(:geom), 4326));
    """
    )

    for coord in coordinates:
        db_session.execute(query, {"id": coord.id, "geom": coord.coordinate})
    db_session.commit()

    first_coordinate: Coordinate = db_session.get(Coordinate, 1)
    second_coordinate = db_session.get(Coordinate, 2)
    missing_coordinate = db_session.get(Coordinate, 3)

    assert first_coordinate is not None
    assert first_coordinate.longitude == 8.645
    assert first_coordinate.latitude == 50.123

    assert second_coordinate is not None
    assert second_coordinate.x == 7.46
    assert second_coordinate.y == 51.5

    assert missing_coordinate is None


@pytest.mark.docker_required
def test_create_weather_value(db_session):
    """Test creating a weather value."""
    berlin = Coordinate.from_xy(id=1, x=13.405, y=52.52)

    query = text(
        """
        INSERT INTO coordinate (id, coordinate)
        VALUES (:id, ST_SetSRID(ST_GeomFromWKB(:geom), 4326));
    """
    )

    db_session.execute(query, {"id": berlin.id, "geom": berlin.coordinate})
    db_session.commit()

    now = datetime.now()
    weather = WeatherValue(
        time=now,
        coordinate_id=berlin.id,
        aswdifd_s=210.5,
        aswdir_s=620.3,
        t2m=293.15,  # 20°C in Kelvin
        u131m=5.5,
        v131m=2.2,
    )
    db_session.add(weather)
    db_session.commit()

    retrieved = db_session.exec(
        select(WeatherValue).where(
            WeatherValue.time == now, WeatherValue.coordinate_id == berlin.id
        )
    ).first()

    assert retrieved is not None
    assert retrieved.coordinate_id == berlin.id
    assert abs(retrieved.temperature - 20.0) < 0.1  # t2m - 273.15
    assert retrieved.diffuse_irradiance == 210.5
    assert retrieved.direct_irradiance == 620.3
