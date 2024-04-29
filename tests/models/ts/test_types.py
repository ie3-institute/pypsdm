import pandas as pd

from pypsdm.models.ts.base import TIME_COLUMN_NAME, EntityKey
from pypsdm.models.ts.types import (
    ComplexPower,
    ComplexPowerDict,
    ComplexPowerWithSoc,
    ComplexVoltage,
    ComplexVoltageDict,
    ComplexVoltagePower,
)


def get_complex_power():
    data = pd.DataFrame(
        {
            TIME_COLUMN_NAME: [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
            ],
            "p": [0.0, 1.0, -2.0, 3.0],
            "q": [0.0, -1.0, 2.0, 3.0],
        },
    )
    return ComplexPower(data)


def get_power_dict():
    dct = {
        EntityKey("a"): get_complex_power(),
        EntityKey("b"): get_complex_power(),
        EntityKey("c"): get_complex_power(),
    }
    return ComplexPowerDict(dct)


def test_add():
    s = get_complex_power()
    res = s + s
    pd.testing.assert_series_equal(res.p, s.p * 2)
    pd.testing.assert_series_equal(res.q, s.q * 2)

    res = s + ComplexPower.empty()
    pd.testing.assert_series_equal(res.p, s.p)
    pd.testing.assert_series_equal(res.q, s.q)


def test_sub():
    s = get_complex_power()
    res = s - s
    pd.testing.assert_series_equal(res.p, s.p * 0)
    pd.testing.assert_series_equal(res.q, s.q * 0)

    res = s - ComplexPower.empty()
    pd.testing.assert_series_equal(res.p, s.p)
    pd.testing.assert_series_equal(res.q, s.q)


def test_mul():
    s = get_complex_power()
    res = s * 2
    pd.testing.assert_series_equal(res.p, s.p * 2)
    pd.testing.assert_series_equal(res.q, s.q * 2)

    res = s * 0
    pd.testing.assert_series_equal(res.p, s.p * 0)
    pd.testing.assert_series_equal(res.q, s.q * 0)


def get_sample_data_soc():
    data = pd.DataFrame(
        {
            TIME_COLUMN_NAME: [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
            ],
            "p": [0.0, 1.0, -2.0, 3.0],
            "q": [0.0, -1.0, 2.0, 3.0],
            "soc": [10.0, 20.0, 30.0, 40.0],
        },
    )
    return ComplexPowerWithSoc(data)


def test_add_with_soc():
    s = get_sample_data_soc()
    s_b = get_sample_data_soc()
    res = s.add_with_soc(10, s_b, 5)
    pd.testing.assert_series_equal(res.soc, s_b.soc)

    s_b.data["soc"] = s_b.data["soc"] * 1 / 2
    res = s.add_with_soc(10, s_b, 10)
    expectd_soc = (s.soc + s_b.soc) * 1 / 2
    pd.testing.assert_series_equal(res.soc, expectd_soc)


def test_p():
    dct = get_power_dict()
    res = dct.p()
    res.columns = ["a", "b", "c"]
    assert res.shape == (4, 3)


def test_q():
    dct = get_power_dict()
    res = dct.q()
    res.columns = ["a", "b", "c"]
    assert res.shape == (4, 3)


def get_voltage_data():
    data = pd.DataFrame(
        {
            TIME_COLUMN_NAME: [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
            ],
            "v_mag": [0.0, 1.0, -2.0, 3.0],
            "v_ang": [0.0, -1.0, 2.0, 3.0],
        },
    )
    return ComplexVoltage(data)


def get_voltage_dict():
    dct = {
        EntityKey("a"): get_voltage_data(),
        EntityKey("b"): get_voltage_data(),
        EntityKey("c"): get_voltage_data(),
    }
    return ComplexVoltageDict(dct)


def test_v_mag():
    dct = get_voltage_dict()
    v_mag = dct.v_mag()
    dct.v_mag()
    assert v_mag.columns.tolist() == ["a", "b", "c"]


def test_v_ang():
    dct = get_voltage_dict()
    v_ang = dct.v_ang()
    assert v_ang.columns.tolist() == ["a", "b", "c"]


def test_v_complex():
    dct = get_voltage_dict()
    v_complex = dct.v_complex()
    assert v_complex.columns.tolist() == ["a", "b", "c"]


def get_voltage_power_data():
    data = pd.DataFrame(
        {
            TIME_COLUMN_NAME: [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
            ],
            "v_mag": [0.0, 1.0, -2.0, 3.0],
            "v_ang": [0.0, -1.0, 2.0, 3.0],
            "p": [0.0, 1.0, -2.0, 3.0],
            "q": [0.0, -1.0, 2.0, 3.0],
        },
    )
    return ComplexVoltagePower(data)


def test_voltage_power():
    vp = get_voltage_power_data()
    v = vp.as_complex_voltage()
    pd.testing.assert_series_equal(vp.v_mag, v.v_mag)
