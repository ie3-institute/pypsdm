def test_transformers_2_w_result(gwr):
    t_res = gwr.results.transformers_2w
    t_uuids = set(t_res.uuids())
    expected_t_res_len = 9
    assert len(t_res) == expected_t_res_len
    assert len(t_res.i_a_ang.columns) == expected_t_res_len
    assert set(t_res.i_a_ang.columns) == t_uuids
    assert len(t_res.i_a_mag.columns) == expected_t_res_len
    assert set(t_res.i_a_mag.columns) == t_uuids
    assert len(t_res.i_b_ang.columns) == expected_t_res_len
    assert set(t_res.i_b_ang.columns) == t_uuids
    assert len(t_res.i_b_mag.columns) == expected_t_res_len
    assert set(t_res.i_b_mag.columns) == t_uuids


def test_transformer_2_w_result(gwr):
    t_res = gwr.results.transformers_2w.results()[0]
    assert set(t_res.data.columns) == set(t_res.attributes())
