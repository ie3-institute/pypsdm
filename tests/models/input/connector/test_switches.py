import pytest

from psdm_analysis.models.input.connector.switches import Switches
from tests.utils import compare_dfs


@pytest.fixture
def switches(input_path, delimiter):
    switches = Switches.from_csv(
        input_path,
        delimiter,
    )
    return switches


def test_closed(switches):
    assert not switches.closed.iloc[0]


def test_to_csv(switches, tmp_path, delimiter):
    switches.to_csv(str(tmp_path), delimiter)
    switches2 = Switches.from_csv(str(tmp_path), delimiter)
    compare_dfs(switches.data, switches2.data)
