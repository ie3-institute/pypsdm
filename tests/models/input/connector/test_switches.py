import pytest

from pypsdm.models.input.connector.switches import Switches
from pypsdm.processing.dataframe import compare_dfs


@pytest.fixture
def switches(input_path):
    switches = Switches.from_csv(
        input_path,
    )
    return switches


def test_closed(switches):
    assert not switches.closed.iloc[0]


def test_to_csv(switches: Switches, tmp_path, delimiter):
    switches.to_csv(str(tmp_path), delimiter)
    switches2 = Switches.from_csv(str(tmp_path), delimiter)
    compare_dfs(switches.data, switches2.data)
