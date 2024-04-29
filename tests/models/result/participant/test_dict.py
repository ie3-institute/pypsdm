import pandas as pd

from pypsdm.models.result.participant.dict import LoadsResult
from pypsdm.models.ts.base import TIME_COLUMN_NAME, EntityKey
from pypsdm.models.ts.types import ComplexPower


def get_power_data():
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


def get_loads_dict():
    dct = {
        EntityKey("a"): get_power_data(),
        EntityKey("b"): get_power_data(),
        EntityKey("c"): get_power_data(),
    }
    return LoadsResult(dct)


def test_init():
    loads = get_loads_dict()
    assert len(loads) == 3
    assert loads.keys() == {EntityKey("a"), EntityKey("b"), EntityKey("c")}


def test_from_csv(tmp_path):
    data_str = """
time,p,q,uuid,input_model
2021-01-01 00:00:00,0.0,0.0,a,a
2021-01-02 00:00:00,1.0,-1.0,a,a
2021-01-03 00:00:00,-2.0,2.0,a,a
2021-01-04 00:00:00,3.0,3.0,a,a
2021-01-01 00:00:00,0.0,0.0,b,b
2021-01-02 00:00:00,1.0,-1.0,b,b
2021-01-03 00:00:00,-2.0,2.0,b,b
2021-01-04 00:00:00,3.0,3.0,b,b
2021-01-01 00:00:00,0.0,0.0,c,c
2021-01-02 00:00:00,1.0,-1.0,c,c
2021-01-03 00:00:00,-2.0,2.0,c,c
2021-01-04 00:00:00,3.0,3.0,c,c
"""
    file_path = tmp_path / "load_res.csv"
    with open(file_path, "w") as f:
        f.write(data_str)
    loads = LoadsResult.from_csv(tmp_path)
    assert set(loads.keys()) == {EntityKey("a"), EntityKey("b"), EntityKey("c")}
    assert loads.keys() == {EntityKey("a"), EntityKey("b"), EntityKey("c")}
    assert set(loads["a"].data.columns) == {"p", "q"}


def test_to_csv(tmp_path):
    loads = get_loads_dict()
    loads.to_csv(tmp_path)
    loads_b = LoadsResult.from_csv(tmp_path)
    assert loads == loads_b
