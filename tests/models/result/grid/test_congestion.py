from pypsdm import EntityKey
from pypsdm.models.result.grid.congestions import CongestionsResult


def test_from_csv(tmp_path):
    data_str = """
input_model,max,min,subgrid,time,type,value
a,1.03,0.97,135,2016-01-02 02:00:00,node,1.0322258973011036
b,1.03,0.97,135,2016-01-02 02:00:00,node,1.0322258973011036
a,1.03,0.97,135,2016-01-04 10:00:00,node,1.032572359547453
b,1.03,0.97,135,2016-01-04 10:00:00,node,1.032572359547453
a,1.03,0.97,135,2016-01-04 11:00:00,node,1.03308051187176
b,1.03,0.97,135,2016-01-04 11:00:00,node,1.032956427498655
"""
    file_path = tmp_path / "congestion_res.csv"
    with open(file_path, "w") as f:
        f.write(data_str)
    congestions = CongestionsResult.from_csv(tmp_path)
    assert set(congestions.keys()) == {EntityKey("a"), EntityKey("b")}
    assert congestions.keys() == {EntityKey("a"), EntityKey("b")}
    assert set(congestions["a"].data.columns) == {
        "max",
        "min",
        "subgrid",
        "type",
        "value",
    }
