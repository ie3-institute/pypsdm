def test_lines_result(gwr):
    lines_res = gwr.results.lines
    lines_uuids = set(lines_res.uuids())
    expected_nr_uuids = len(gwr.grid.raw_grid.lines)
    check_connector_res(lines_res, lines_uuids, expected_nr_uuids)


def check_connector_res(connector_res, connectors_uuids, expected_nr_uuids):
    assert len(connector_res) == expected_nr_uuids
    assert len(connector_res.i_a_ang.columns) == expected_nr_uuids
    assert set(connector_res.i_a_ang.columns) == connectors_uuids
    assert len(connector_res.i_a_mag.columns) == expected_nr_uuids
    assert set(connector_res.i_a_mag.columns) == connectors_uuids
    assert len(connector_res.i_b_ang.columns) == expected_nr_uuids
    assert set(connector_res.i_b_ang.columns) == connectors_uuids
    assert len(connector_res.i_b_mag.columns) == expected_nr_uuids
    assert set(connector_res.i_b_mag.columns) == connectors_uuids


def test_line_result(gwr):
    t_res = gwr.results.lines.results()[0]
    assert set(t_res.data.columns) == set(t_res.attributes())
