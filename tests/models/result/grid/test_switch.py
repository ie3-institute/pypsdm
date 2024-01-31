import pandas as pd

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.grid.switch import SwitchesResult, SwitchResult


def get_switch_result(closed):
    # pd date range
    dates = pd.date_range("20130101", periods=len(closed))
    data = pd.DataFrame(
        {
            "closed": closed,
        },
        index=dates,
    )
    return SwitchResult(RawGridElementsEnum.SWITCH, "test_switch", None, data)


def test_switch_result():
    closed = [True, False, True]
    switch = get_switch_result(closed=closed)
    assert len(switch) == 3
    assert list(switch.closed) == closed


def test_from_csv(result_path):
    switches = SwitchesResult.from_csv(result_path)
    assert len(switches) == 1
    closed = switches.closed
    assert len(closed.columns) == 1
    assert not closed.iloc[0][closed.columns[0]]
