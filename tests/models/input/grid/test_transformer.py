import math

import numpy as np

from pypsdm.models.input.connector.transformer import Transformers2W


def test_to_csv(input_path, tmp_path):
    transformer = Transformers2W.from_csv(input_path)
    transformer.to_csv(tmp_path)
    transformer_b = Transformers2W.from_csv(tmp_path)
    transformer.compare(transformer_b)


def test_gij(simple_grid):
    gij = simple_grid.transformers_2_w.gij()
    uuid = "4ac7f0bd-2ea9-4510-9e71-0da40886d9d3"
    # SIMONA pu result
    nom_imp = 0.266666666666666
    assert math.isclose(gij[uuid], 30.416517485868557 / nom_imp)


def test_bij(simple_grid):
    bij = simple_grid.transformers_2_w.bij()
    uuid = "4ac7f0bd-2ea9-4510-9e71-0da40886d9d3"
    # SIMONA pu result
    nom_imp = 0.266666666666666
    assert math.isclose(bij[uuid], -100.49779444407964 / nom_imp)


def test_g0(simple_grid):
    g0 = simple_grid.transformers_2_w.g0()
    uuid = "4ac7f0bd-2ea9-4510-9e71-0da40886d9d3"
    # SIMONA pu result
    nom_imp = 0.266666666666666
    assert math.isclose(g0[uuid], 0.011000000000000001 / nom_imp)


def test_b0(simple_grid):
    b0 = simple_grid.transformers_2_w.b0()
    uuid = "4ac7f0bd-2ea9-4510-9e71-0da40886d9d3"
    # SIMONA pu result
    nom_imp = 0.266666666666666
    assert math.isclose(b0[uuid], 9.726348184198494 * 1e-5 / nom_imp)


def test_yij(simple_grid):
    yij = simple_grid.transformers_2_w.yij()
    uuid = "4ac7f0bd-2ea9-4510-9e71-0da40886d9d3"
    # SIMONA pu result
    nom_imp = 0.266666666666666
    assert math.isclose(yij[uuid].real, 30.416517485868557 / nom_imp)
    assert math.isclose(yij[uuid].imag, -100.49779444407964 / nom_imp)


def test_y0(simple_grid):
    y0_high = simple_grid.transformers_2_w.y0("high")
    y0_low = simple_grid.transformers_2_w.y0("low")
    uuid = "4ac7f0bd-2ea9-4510-9e71-0da40886d9d3"
    # SIMONA pu result
    nom_imp = 0.266666666666666
    assert math.isclose(y0_high[uuid].real, 0.0055000000000000005 / nom_imp)
    assert math.isclose(y0_high[uuid].imag, 4.863174092099247 * 1e-5 / nom_imp)

    assert math.isclose(y0_low[uuid].real, 0.0055000000000000005 / nom_imp)
    assert math.isclose(y0_low[uuid].imag, 4.86317409209924 * 1e-5 / nom_imp)


def test_admittance_matrix(simple_grid):
    uuid_idx = {
        "b7a5be0d-2662-41b2-99c6-3b8121a75e9e": 2,
        "df97c0d1-379b-417a-a473-8e7fe37da99d": 1,
        "1dcddd06-f41a-405b-9686-7f7942852196": 3,
        "e3c3c6a3-c383-4dbb-9b3f-a14125615386": 0,
        "6a4547a8-630b-46e4-8144-9cd649e67c07": 4,
    }

    Y = simple_grid.transformers_2_w.admittance_matrix(uuid_idx)

    # SIMONA pu result
    nom_imp = 0.266666666666666
    second_row = [
        0,
        30.422017485868558 + 1j * -100.49774581233872,
        0.0,
        0.0,
        -30.416517485868557 + 1j * 100.4977944440796,
    ]

    fifth_row = [
        0,
        -30.416517485868557 + 1j * 100.49779444407964,
        0.0,
        0.0,
        30.422017485868558 + 1j * -100.49774581233872,
    ]

    second_row = [x / nom_imp for x in second_row]
    fifth_row = [x / nom_imp for x in fifth_row]

    assert np.allclose(Y[1], second_row)
    assert np.allclose(Y[4], fifth_row)
