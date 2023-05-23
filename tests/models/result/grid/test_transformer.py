from tests.models.result.grid.test_connector import check_connector_res


def test_transformers_2_w_result(gwr):
    transformers_res = gwr.results.transformers_2w
    transformers_uuids = set(transformers_res.uuids())
    expected_transformers_uuids = 9
    check_connector_res(
        transformers_res, transformers_uuids, expected_transformers_uuids
    )


def test_transformer_2_w_result(gwr):
    t_res = gwr.results.transformers_2w.results()[0]
    assert set(t_res.data.columns) == set(t_res.attributes())
