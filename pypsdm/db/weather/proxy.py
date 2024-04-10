import os
from datetime import datetime
from typing import Optional, Union

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlmodel import Session, select

from pypsdm.db.weather.models import Coordinate, WeatherValue


class WeatherProxy:
    """
    SQLModel based proxy class to access weather database with ICON weather model.
    """

    def __init__(self, engine: Engine | None = None, echo=False):
        """
        When no engine is passed, it looks for system wide or .env based environment
        variables.

        Expected environment variables:
            - WEATHER_DB_USER
            - WEATHER_DB_PASSWORD
            - WEATHER_DB_HOST
            - WEATHER_DB_PORT
            - WEATHER_DB_NAME
        """
        if not engine:
            engine = create_engine_from_env(echo)
        self.engine = engine

    def get_weather(self, time: datetime, coordinate_id: int) -> Optional[WeatherValue]:
        with Session(self.engine) as session:
            statement = select(WeatherValue).where(
                WeatherValue.time == time, WeatherValue.coordinate_id == coordinate_id
            )
            result = session.exec(statement).first()
            return result

    def get_weather_for_interval(
        self, start: datetime, stop: datetime, coordinate_id: int | set[int]
    ) -> list[WeatherValue]:
        with Session(self.engine) as session:

            if isinstance(coordinate_id, int):
                statement = select(WeatherValue).where(
                    WeatherValue.time >= start,  # type: ignore
                    WeatherValue.time <= stop,  # type: ignore
                    WeatherValue.coordinate_id == coordinate_id,
                )
            elif isinstance(coordinate_id, set):
                statement = select(WeatherValue).where(
                    WeatherValue.time >= start,  # type: ignore
                    WeatherValue.time <= stop,  # type: ignore
                    WeatherValue.coordinate_id.in_(coordinate_id),  # type: ignore
                )
            result = session.exec(statement).all()
            return list(result)

    def get_coordinate_by_id(self, coordinate_id: int) -> Optional[Coordinate]:
        with Session(self.engine) as session:
            statement = select(Coordinate).where(Coordinate.id == coordinate_id)
            result = session.exec(statement).first()
            return result

    def get_closest_coordinates(
        self,
        x: float,
        y: float,
        n: int,
        schema_name="public",
        table_name="coordinate",
        id_column="id",
        point_column="coordinate",
    ) -> list[tuple[Coordinate, float]]:
        query = _create_query_n_nearest_points(
            x, y, n, schema_name, table_name, id_column, point_column
        )
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            coords = []
            for r in result:
                coord = Coordinate(id=r.id, coordinate=r.coordinate)
                coords.append((coord, r.distance))
            return coords


def _create_query_n_nearest_points(
    x: float,
    y: float,
    n: int,
    schema_name="public",
    table_name="coordinate",
    id_column="id",
    point_column="coordinate",
):
    query = f"""
    SELECT
        {id_column} AS id,
        {point_column} AS coordinate,
        {point_column} <-> ST_Point({x}, {y}) AS distance
    FROM
        {schema_name}."{table_name}"
    ORDER BY distance
    LIMIT {n};
    """
    return query


def create_engine_from_env(echo=False) -> Engine:
    load_dotenv()
    username = os.getenv("WEATHER_DB_USER")
    password = os.getenv("WEATHER_DB_PASSWORD")
    host = os.getenv("WEATHER_DB_HOST")
    port = os.getenv("WEATHER_DB_PORT")
    database = os.getenv("WEATHER_DB_NAME")
    DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    return create_engine(DATABASE_URL, echo=echo)


def create_engine_from_params(
    username: str, password: str, host: str, port: str, database: str, echo=False
) -> Engine:
    return create_engine(
        f"postgresql://{username}:{password}@{host}:{port}/{database}", echo=echo
    )


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
