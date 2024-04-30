import pandas as pd

from pypsdm.models.result.grid.transformer import (
    Transformer2WResult,
    Transformers2WResult,
)
from pypsdm.models.ts.base import TIME_COLUMN_NAME, EntityKey


def get_trafo_data():
    # Create a DataFrame with specified data using fixed values
    data = pd.DataFrame(
        {
            TIME_COLUMN_NAME: ["2021-01-01", "2021-01-02", "2021-01-03", "2021-01-04"],
            "i_a_ang": [30, -45, 60, 90],  # Fixed angles in degrees
            "i_a_mag": [50, 75, 65, 80],  # Fixed magnitudes
            "i_b_ang": [-30, 45, -60, -90],
            "i_b_mag": [55, 70, 60, 85],
            "tap_pos": [1, 2, 3, 4],  # Fixed tap positions
        }
    )
    return Transformer2WResult(data)


def test_from_csv(tmp_path):
    # Create a CSV file with specified data
    data_str = """
time,i_a_ang,i_a_mag,i_b_ang,i_b_mag,tap_pos,input_model
2021-01-01 00:00:00,30,50,-30,55,1,a
2021-01-02 00:00:00,-45,75,45,70,2,a
2021-01-03 00:00:00,60,65,-60,60,3,a
2021-01-04 00:00:00,90,80,-90,85,4,a
2021-01-01 00:00:00,30,50,-30,55,1,b
2021-01-02 00:00:00,-45,75,45,70,2,b
2021-01-03 00:00:00,60,65,-60,60,3,b
2021-01-04 00:00:00,90,80,-90,85,4,b
2021-01-01 00:00:00,30,50,-30,55,1,c
2021-01-02 00:00:00,-45,75,45,70,2,c
2021-01-03 00:00:00,60,65,-60,60,3,c
2021-01-04 00:00:00,90,80,-90,85,4,c
"""
    file_path = tmp_path / "transformer_2_w_res.csv"
    with open(file_path, "w") as f:
        f.write(data_str)
    trafos = Transformers2WResult.from_csv(tmp_path)
    assert set(trafos.keys()) == {EntityKey("a"), EntityKey("b"), EntityKey("c")}
    assert trafos.keys() == {EntityKey("a"), EntityKey("b"), EntityKey("c")}
