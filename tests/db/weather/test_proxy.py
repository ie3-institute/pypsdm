import math

from pypsdm.db.weather.models import Coordinate
from pypsdm.db.weather.utils import weighted_interpolation_coordinates


def test_weighted_interpolation_coordinates(db_session):
    """Test weighted interpolation of coordinates."""
    coordinates = [
        Coordinate.from_wkb_hex(
            id=13890,
            coordinate="0101000020E610000000000000008026400000000000E04A40",
        ),
        Coordinate.from_wkb_hex(
            id=13891,
            coordinate="0101000020E610000000000000000027400000000000E04A40",
        ),
        Coordinate.from_wkb_hex(
            id=14079,
            coordinate="0101000020E610000000000000008026400000000000C04A40",
        ),
        Coordinate.from_wkb_hex(
            id=14080,
            coordinate="0101000020E610000000000000000027400000000000C04A40",
        ),
        Coordinate.from_wkb_hex(
            id=13889,
            coordinate="0101000020E610000000000000000026400000000000E04A40",
        ),
        Coordinate.from_wkb_hex(
            id=13892,
            coordinate="0101000020E610000000000000008027400000000000E04A40",
        ),
        Coordinate.from_wkb_hex(
            id=14078,
            coordinate="0101000020E610000000000000000026400000000000C04A40",
        ),
        Coordinate.from_wkb_hex(
            id=14081,
            coordinate="0101000020E610000000000000008027400000000000C04A40",
        ),
    ]

    db_session.add_all(coordinates)
    db_session.commit()
    long, lat = 11.3692, 53.6315

    nearest_coordinates = [
        (db_session.get(Coordinate, coord.id), weight)
        for coord, weight in zip(
            coordinates,
            [
                15336.967985536437,
                15741.508288878984,
                16606.405396805483,
                16982.92952636213,
                27650.80452994915,
                28324.62399357631,
                28429.952194089583,
                29089.579082292785,
            ],
        )
    ]

    closest = weighted_interpolation_coordinates((long, lat), nearest_coordinates)

    closest_ids = [c[0].id for c in closest]

    assert set(closest_ids) == {13890, 13891, 14079, 14080}
    assert math.isclose(sum([c[1] for c in closest]), 1)
