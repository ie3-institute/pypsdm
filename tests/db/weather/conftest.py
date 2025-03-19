import platform
import subprocess
import time

import pytest
import sqlalchemy
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Docker tests skipped on Windows"
)
def docker_postgres():
    """Start a PostgreSQL container for testing."""
    container_name = "test_postgres_container"

    # Check if the container already exists
    check_cmd = [
        "docker",
        "ps",
        "-a",
        "--filter",
        f"name={container_name}",
        "--format",
        "{{.Names}}",
    ]
    result = subprocess.run(check_cmd, capture_output=True, text=True)

    if container_name in result.stdout:
        # Remove existing container
        subprocess.run(["docker", "rm", "-f", container_name], check=True)

    # Start a new container
    run_cmd = [
        "docker",
        "run",
        "--name",
        container_name,
        "-e",
        "POSTGRES_USER=postgres",
        "-e",
        "POSTGRES_PASSWORD=postgres",
        "-e",
        "POSTGRES_DB=test_db",
        "-p",
        "5433:5432",
        "-d",
        "postgis/postgis:17-3.4",
    ]
    subprocess.run(run_cmd, check=True)

    # Wait for the database to be ready
    time.sleep(5)

    yield "postgresql://postgres:postgres@localhost:5433/test_db"

    # Cleanup
    subprocess.run(["docker", "rm", "-f", container_name], check=True)


@pytest.fixture(scope="session")
def db_engine(docker_postgres):
    """Create a database engine connected to the Docker PostgreSQL instance."""
    engine = create_engine(docker_postgres)

    # Try connecting multiple times with increasing delays
    max_retries = 5
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            # Enable PostGIS
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.commit()

            # If we get here, connection was successful
            break

        except sqlalchemy.exc.OperationalError as e:
            if attempt < max_retries - 1:
                print(
                    f"Connection attempt {attempt + 1} failed. Retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise Exception(
                    f"Failed to connect after {max_retries} attempts"
                ) from e

    # Create tables
    SQLModel.metadata.create_all(engine)

    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a new database session for a test."""
    with Session(db_engine) as session:
        yield session
        session.rollback()  # Rollback after each test


@pytest.fixture(scope="function", autouse=True)
def reset_db(db_engine):
    SQLModel.metadata.drop_all(db_engine)
    SQLModel.metadata.create_all(db_engine)
