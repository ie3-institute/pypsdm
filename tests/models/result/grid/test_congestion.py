import pandas as pd

from pypsdm.models.result.grid.congestions import CongestionsResult, CongestionResult
from pypsdm.models.ts.base import SubGridKey, TIME_COLUMN_NAME


def test_from_csv(tmp_path):
    data_str = """
v_max,v_min,line,subgrid,time,transformer,voltage
1.05,0.95,false,1,2016-07-24T01:00:00Z,false,false
1.05,0.95,false,4,2016-07-24T01:00:00Z,false,false
1.05,0.95,false,2,2016-07-24T01:00:00Z,false,false
1.05,0.95,false,3,2016-07-24T01:00:00Z,false,true
1.05,0.95,false,5,2016-07-24T01:00:00Z,false,false
1.05,0.95,false,1,2016-07-24T02:00:00Z,false,false
1.05,0.95,false,2,2016-07-24T02:00:00Z,false,false
1.05,0.95,false,3,2016-07-24T02:00:00Z,false,true
1.05,0.95,false,4,2016-07-24T02:00:00Z,false,false
1.05,0.95,false,5,2016-07-24T02:00:00Z,false,false
"""
    file_path = tmp_path / "congestion_res.csv"
    with open(file_path, "w") as f:
        f.write(data_str)

    congestions = CongestionsResult.from_csv(tmp_path)
    assert set(congestions.keys()) == {SubGridKey(1), SubGridKey(2), SubGridKey(3), SubGridKey(4), SubGridKey(5)}
    print(set(congestions[1].data.columns))
    assert set(congestions[1].data.columns) == {"v_max", "transformer", "voltage", "subgrid", "v_min", "line"}


def test_to_csv(tmp_path):
    def get_congestion_data(subgrid: int):
        data = pd.DataFrame(
            {
                TIME_COLUMN_NAME: [
                    "2021-01-01",
                    "2021-01-02",
                    "2021-01-03",
                    "2021-01-04",
                ],
            }
        )
        data["vMin"] = [0.9, 0.9, 0.9, 0.9]
        data["vMax"] = [1.1, 1.1, 1.1, 1.1]
        data["subgrid"] = [subgrid, subgrid, subgrid, subgrid]

        for attr in ["voltage", "line", "transformer"]:
            data[attr] = [False, False, False, False]
        return data

    res_dict = {SubGridKey(s): CongestionResult(get_congestion_data(s)) for s in [1, 2, 3]}

    congestions = CongestionsResult(res_dict)

    congestions.to_csv(tmp_path)
    congestions2 = CongestionsResult.from_csv(tmp_path)
    assert congestions == congestions2

