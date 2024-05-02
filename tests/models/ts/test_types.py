from datetime import datetime

import pandas as pd

from pypsdm.db.weather.models import WeatherValue
from pypsdm.models.ts.base import TIME_COLUMN_NAME, EntityKey
from pypsdm.models.ts.types import (
    ComplexPower,
    ComplexPowerDict,
    ComplexPowerWithSoc,
    ComplexVoltage,
    ComplexVoltageDict,
    ComplexVoltagePower,
    CoordinateWeather,
    WeatherDict,
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


def test_weather_from_value_list():
    weather_value1 = WeatherValue(
        time=datetime(2021, 1, 1, 0, 0),
        coordinate_id=1,
        aswdifd_s=1,
        aswdir_s=2,
        t2m=3,
        u131m=4,
        v131m=5,
    )
    weather_value2 = WeatherValue(
        time=datetime(2021, 1, 1, 2, 0),
        coordinate_id=1,
        aswdifd_s=6,
        aswdir_s=7,
        t2m=8,
        u131m=9,
        v131m=10,
    )

    values = [weather_value1, weather_value2]
    df = CoordinateWeather.df_from_value_list(values)
    expected_cols = set(CoordinateWeather.attributes())
    expected_cols.add("coordinate_id")
    assert set(df.columns) == expected_cols
    assert set(df.index) == set([weather_value1.time, weather_value2.time])

    weather_value2.coordinate_id = 2
    dct = WeatherDict.from_value_list(values)
    assert set(dct.keys()) == set([1, 2])


def test_weather_add_mult():
    data = pd.DataFrame(
        {
            "diffuse_irradiance": [1, 2, 3],
            "direct_irradiance": [4, 5, 6],
            "temperature": [7, 8, 9],
            "wind_velocity_u": [10, 11, 12],
            "wind_velocity_v": [13, 14, 15],
        },
        index=pd.date_range("2021-01-01", periods=3, freq="H"),
    )
    data.index.name = TIME_COLUMN_NAME
    weather = CoordinateWeather(data)
    weather2 = CoordinateWeather(data)
    res = weather + weather2
    pd.testing.assert_frame_equal(res.data, data * 2, check_dtype=False)
    res = weather + CoordinateWeather.empty()
    pd.testing.assert_frame_equal(res.data, data, check_dtype=False)
