import os

import pytest

from definitions import ROOT_DIR


@pytest.fixture(scope="session")
def resources_path():
    return os.path.join(ROOT_DIR, "tests", "resources")


@pytest.fixture(scope="session")
def input_path():
    return os.path.join(ROOT_DIR, "tests", "resources", "vn_simona", "input")


@pytest.fixture(scope="session")
def input_path_sg():
    return os.path.join(ROOT_DIR, "tests", "resources", "simple_grid", "input")


@pytest.fixture(scope="session")
def input_path_sb():
    return os.path.join(ROOT_DIR, "tests", "resources", "simbench", "input")


@pytest.fixture(scope="session")
def result_path_sb():
    return os.path.join(ROOT_DIR, "tests", "resources", "simbench", "results")


@pytest.fixture(scope="session")
def result_path():
    return os.path.join(ROOT_DIR, "tests", "resources", "vn_simona", "results")
