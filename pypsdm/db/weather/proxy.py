import os
from datetime import datetime
from typing import Optional

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
        When no engine is passed, it looks for system-wide or .env based environment
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
        n: int,  # amount of closest coordinates to return
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
    try:
        return create_engine(DATABASE_URL, echo=echo)
    except Exception as e:
        raise ValueError(
            f"Failed to create engine with database url: {DATABASE_URL}"
        ) from e


def create_engine_from_params(
    username: str, password: str, host: str, port: str, database: str, echo=False
) -> Engine:
    return create_engine(
        f"postgresql://{username}:{password}@{host}:{port}/{database}", echo=echo
    )
