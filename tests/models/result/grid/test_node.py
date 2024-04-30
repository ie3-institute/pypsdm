from pypsdm.models.result.grid.node import NodesResult
from pypsdm.models.ts.base import EntityKey


def test_from_csv(tmp_path):
    data_str = """
time,v_mag,v_ang,uuid,input_model
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
    file_path = tmp_path / "node_res.csv"
    with open(file_path, "w") as f:
        f.write(data_str)
    nodes = NodesResult.from_csv(tmp_path)
    assert set(nodes.keys()) == {EntityKey("a"), EntityKey("b"), EntityKey("c")}
    assert nodes.keys() == {EntityKey("a"), EntityKey("b"), EntityKey("c")}
    assert set(nodes["a"].data.columns) == {"v_mag", "v_ang"}
