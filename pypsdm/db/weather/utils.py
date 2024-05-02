import concurrent.futures
from datetime import datetime

from pypsdm.db.weather.models import Coordinate
from pypsdm.db.weather.proxy import WeatherProxy
from pypsdm.models.input.node import Nodes
from pypsdm.models.ts.types import CoordinateWeather, WeatherDict


def get_nodal_weighted_weather(
    nodes: Nodes, start: datetime, end: datetime, weather: WeatherProxy
) -> WeatherDict:
    weighted_coordinates = nodal_weighted_coordinates(nodes=nodes, weather=weather)
    coordinates = set()
    for wc in weighted_coordinates.values():
        coordinates.update([c[0].id for c in wc])
    values = weather.get_weather_for_interval(start, end, coordinates)
    weather_dct = WeatherDict.from_value_list(values)

    weighted_weather_dct = {}
    for node_id, wc in weighted_coordinates.items():
        weighted_weather = CoordinateWeather.empty()
        for c, w in wc:
            weighted_weather += weather_dct[c.id] * w
        weighted_weather_dct[node_id] = weighted_weather

    return WeatherDict(weighted_weather_dct)


def nodal_weighted_coordinates(
    nodes: Nodes, weather: WeatherProxy
) -> dict[str, list[tuple[Coordinate, float]]]:
    """
    Determine the 4 nearest coordinates (each in one of the surrounding quadrants) for
    each of the nodes and weigh them by their distance (sum of the weights = 1).

    Args:
        nodes (Nodes): Nodes object containing the nodes
        weather (WeatherProxy): WeatherProxy object to access the weather database

    Returns:
        dict[str, list[tuple[Coordinate, float]]]: Dictionary with node uuids as keys
            and a list of tuples with the nearest coordinates and their weights as values
    """
    nodes_uuid = nodes.uuid
    weighted_coordinates = {}

    def fetch_and_weight_coordinates(node: str, nodes: Nodes, weather: WeatherProxy):
        lon, lat = nodes.data.loc[node, ["longitude", "latitude"]]  # type: ignore
        closest = weather.get_closest_coordinates(lon, lat, 8)
        weighted_coord = weighted_interpolation_coordinates((lon, lat), closest)
        return node, weighted_coord

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_node = {
            executor.submit(fetch_and_weight_coordinates, node, nodes, weather): node
            for node in nodes_uuid
        }

        for future in concurrent.futures.as_completed(future_to_node):
            node = future_to_node[future]
            try:
                node, weighted_coord = future.result()
                weighted_coordinates[node] = weighted_coord
            except Exception as exc:
                print(f"Node {node} generated an exception: {exc}")
    return weighted_coordinates


def weighted_interpolation_coordinates(
    target: tuple[float, float],
    nearest_coords: list[tuple[Coordinate, float]],
) -> list[tuple[Coordinate, float]]:
    """
    Given a list of nearest surrounding cordinates with respect to a target coordinate,
    find the nearest coordinate in each quadrant and weigh them by their distance to
    the target.

    Requires at least one coordinate in each quadrant (meaing top left, top right,
    bottom left, bottom right).

    Note that the nearest coordinates can be found with the find n closest functionality
    of the WeatherProxy.

    Args:
        target (tuple[float, float]): Target coordinate (x (longitude), y (latitude))
        nearest_coords (list[tuple[Coordinate, float]]): List of nearest coordinates
            with their distances to the target
    """

    x, y = target

    # Check if the queried coordinate is surrounded in each quadrant
    quadrants: list[tuple[Coordinate | None, float]] = [
        (None, float("inf")) for _ in range(4)
    ]  # [Q1, Q2, Q3, Q4]
    for point, distance in nearest_coords:

        if point.x < x and point.y > y:
            if quadrants[0][0]:
                if distance < quadrants[0][1]:
                    quadrants[0] = (point, distance)
            else:
                quadrants[0] = (point, distance)

        if point.x > x and point.y > y:
            if quadrants[1][0]:
                if distance < quadrants[1][1]:
                    quadrants[1] = (point, distance)
            else:
                quadrants[1] = (point, distance)

        if point.x < x and point.y < y:
            if quadrants[2][0]:
                if distance < quadrants[2][1]:
                    quadrants[2] = (point, distance)
            else:
                quadrants[2] = (point, distance)

        if point.x > x and point.y < y:
            if quadrants[3][0]:
                if distance < quadrants[3][1]:
                    quadrants[3] = (point, distance)
            else:
                quadrants[3] = (point, distance)

    acc_dist = 0
    for q in quadrants:
        if q[0]:
            acc_dist += q[1]
        else:
            raise ValueError("Not all quadrants are filled")

    n = len(quadrants)
    weighted_coordinates = []
    for q in quadrants:
        if q[0]:
            weight = (1 - (q[1] / acc_dist)) / (n - 1)
            weighted_coordinates.append((q[0], weight))

    return weighted_coordinates
