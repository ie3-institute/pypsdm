from pypsdm.db.weather.models import Coordinate
from pypsdm.db.weather.utils import weighted_interpolation_coordinates


def test_weighted_interpolation_coordinates():
    target = (0, 0)

    coord1 = Coordinate.from_xy(id=1, x=1, y=1)
    coord2 = Coordinate.from_xy(id=2, x=-1, y=1)
    coord3 = Coordinate.from_xy(id=3, x=1, y=-1)
    coord4 = Coordinate.from_xy(id=4, x=-1, y=-1)
    coord5 = Coordinate.from_xy(id=5, x=-2, y=-2)

    # Calculate distances manually for the test setup
    nearest_coords = [
        (coord2, 1.414),
        (coord1, 1.414),
        (coord4, 1.414),
        (coord3, 1.414),
        (coord5, 2.828),
    ]

    result = weighted_interpolation_coordinates(target, nearest_coords)

    expected_weight = 0.25
    expected = [
        (coord2, expected_weight),
        (coord1, expected_weight),
        (coord4, expected_weight),
        (coord3, expected_weight),
    ]

    # Verify that the function returns the expected results
    assert sorted(result, key=lambda x: x[0].id) == sorted(
        expected, key=lambda x: x[0].id
    ), "Weights or coordinates do not match expected values"
