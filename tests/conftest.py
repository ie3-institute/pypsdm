import os
from datetime import datetime

import pytest

from definitions import ROOT_DIR
from pypsdm.models.gwr import GridWithResults
from pypsdm.models.input.container.grid import GridContainer


@pytest.fixture(scope="session")
def resources_path():
    return os.path.join(ROOT_DIR, "tests", "resources")


@pytest.fixture(scope="session")
def input_path():
    return os.path.join(ROOT_DIR, "tests", "resources", "vn_simona", "input")


@pytest.fixture(scope="session")
def result_path():
    return os.path.join(ROOT_DIR, "tests", "resources", "vn_simona", "results")


@pytest.fixture(scope="session")
def simulation_start():
    return datetime(year=2011, month=1, day=1, hour=12)


@pytest.fixture(scope="session")
def simulation_end():
    return datetime(year=2012, month=2, day=3, hour=4, minute=15)


@pytest.fixture(scope="session")
def gwr(input_path, result_path, simulation_end) -> GridWithResults:
    return GridWithResults.from_csv(
        input_path,
        result_path,
        simulation_end=simulation_end,
    )


@pytest.fixture(scope="session")
def grid(input_path) -> GridContainer:
    return GridContainer.from_csv(
        input_path,
    )


@pytest.fixture(scope="session")
def simple_grid(resources_path) -> GridContainer:
    return GridContainer.from_csv(
        os.path.join(resources_path, "simple_grid", "input"),
    )
