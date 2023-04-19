import os
from datetime import datetime

import pytest

from definitions import ROOT_DIR
from psdm_analysis.models.grid_with_results import GridWithResults
from psdm_analysis.models.input.container.grid_container import GridContainer

# Note: the fixture scope defines how long the fixture is valid and prevents reevaluation


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
def delimiter():
    return ","


@pytest.fixture(scope="session")
def gwr(
    input_path, result_path, simulation_start, simulation_end, delimiter
) -> GridWithResults:
    return GridWithResults.from_csv(
        "vn_simona",
        input_path,
        delimiter,
        result_path,
        delimiter,
        simulation_end=simulation_end,
    )


@pytest.fixture(scope="session")
def grid(input_path, delimiter) -> GridWithResults:
    return GridContainer.from_csv(
        input_path,
        delimiter,
    )
