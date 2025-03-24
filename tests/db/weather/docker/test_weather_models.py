from datetime import datetime

import pytest

from pypsdm.db.weather.models import Coordinate, WeatherValue


@pytest.mark.docker_required
def test_create_coordinate(db_session):
    """Test creating a coordinate."""
    coordinates = []
    coord_1 = Coordinate.from_xy(1, 8.645, 50.123)
    coord_2 = Coordinate.from_xy(2, 7.46, 51.5)
    coordinates: list[Coordinate] = coordinates + [coord_1, coord_2]

    for coord in coordinates:
        db_session.add(coord)
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
    berlin = Coordinate.from_xy(id=4, x=13.405, y=52.52)

    db_session.add(berlin)
    db_session.commit()

    now = datetime.now()
    weather = WeatherValue(
        time=now,
        coordinate_id=berlin.id,
        aswdifd_s=210.5,
        aswdir_s=620.3,
        t2m=293.15,
        u131m=5.5,
        v131m=2.2,
    )
    db_session.add(weather)
    db_session.commit()

    weather_value = db_session.get(WeatherValue, (weather.time, weather.coordinate_id))

    assert weather_value is not None
    assert weather_value.coordinate_id == berlin.id
    assert abs(weather_value.temperature - 20.0) < 0.1
    assert weather_value.diffuse_irradiance == 210.5
    assert weather_value.direct_irradiance == 620.3
