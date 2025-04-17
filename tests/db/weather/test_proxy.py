import math

from pypsdm.db.weather.models import Coordinate
from pypsdm.db.weather.utils import weighted_interpolation_coordinates


def test_weighted_interpolation_coordinates():
    nearest_coordinates = [
        (
            Coordinate.from_xy(13890, 11.25, 53.75),
            15336.967985536437,
        ),
        (
            Coordinate.from_xy(13891, 11.5, 53.75),
            15741.508288878984,
        ),
        (
            Coordinate.from_xy(14079, 11.25, 53.5),
            16606.405396805483,
        ),
        (
            Coordinate.from_xy(14080, 11.5, 53.5),
            16982.92952636213,
        ),
        (
            Coordinate.from_xy(13889, 11.0, 53.75),
            27650.80452994915,
        ),
        (
            Coordinate.from_xy(13892, 11.75, 53.75),
            28324.62399357631,
        ),
        (
            Coordinate.from_xy(14078, 11.0, 53.5),
            28429.952194089583,
        ),
        (
            Coordinate.from_xy(14081, 11.75, 53.5),
            29089.579082292785,
        ),
    ]

    long, lat = 11.3692, 53.6315
    closest = weighted_interpolation_coordinates((long, lat), nearest_coordinates)
    closest_ids = [c[0].id for c in closest]
    assert closest_ids == [13890, 13891, 14079, 14080]
    assert math.isclose(sum([c[1] for c in closest]), 1)
