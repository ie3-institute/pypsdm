import warnings

import pytest

from definitions import ROOT_DIR
from pypsdm.models.gwr import GridWithResults
from pypsdm.plots.grid import (
    BASE_MAPS,
    _get_colormap_color,
    _get_lons_lats,
    _mapbox_style_to_base_map,
    _process_colormap_values,
    grid_plot,
)


@pytest.fixture(scope="module")
def gwr():
    return GridWithResults.from_csv(
        f"{ROOT_DIR}/tests/resources/simbench/input",
        f"{ROOT_DIR}/tests/resources/simbench/results",
    )


@pytest.fixture(scope="module")
def filtered_data(gwr):
    return (
        gwr.lines_res.utilisation(gwr.lines, side="a")
        .loc[["2016-01-02 12:00:00"]]
        .to_dict()
    )


def test_grid_plot_default(gwr):
    fig = grid_plot(gwr.grid)
    assert len(fig.data) > 0
    assert fig.layout.geo.scope == "world"
    assert fig.layout.geo.center is not None
    assert fig.layout.geo.lataxis.range is not None
    assert fig.layout.geo.lonaxis.range is not None


def test_grid_plot_highlights(gwr):
    from pypsdm.plots.common.utils import RED, YELLOW

    lines = gwr.lines.uuid.to_list()[0:2]
    nodes = gwr.nodes.uuid.to_list()[0:2]
    fig = grid_plot(
        gwr.grid,
        line_highlights={RED: lines},
        node_highlights={YELLOW: nodes},
        highlight_disconnected=True,
    )
    assert len(fig.data) > 0


def test_grid_plot_line_colormap(gwr, filtered_data):
    fig = grid_plot(
        gwr.grid,
        cmap_lines="fixed_line_rating_scale",
        cmap_line_values=filtered_data,
        cbar_line_title="Line Utilisation",
    )
    assert len(fig.data) > 0


def test_grid_plot_node_colormap(gwr):
    node_values = {uuid: 1.0 for uuid in gwr.nodes.uuid.to_list()[:3]}
    fig = grid_plot(gwr.grid, cmap_nodes="Rainbow", cmap_node_values=node_values)
    assert len(fig.data) > 0


def test_grid_plot_base_maps(gwr):
    for name in BASE_MAPS:
        fig = grid_plot(gwr.grid, base_map=name)
        assert fig.layout.geo.landcolor == BASE_MAPS[name]["landcolor"]


def test_grid_plot_unknown_base_map_raises(gwr):
    with pytest.raises(ValueError, match="Unknown base_map"):
        grid_plot(gwr.grid, base_map="does-not-exist")


def test_grid_plot_mapbox_style_deprecated(gwr):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fig = grid_plot(gwr.grid, mapbox_style="white-bg")
    assert any(issubclass(x.category, DeprecationWarning) for x in w)
    assert fig.layout.geo.landcolor == BASE_MAPS["white"]["landcolor"]


def test_grid_plot_no_warning_without_mapbox_style(gwr):
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        grid_plot(gwr.grid)


def test_mapbox_style_to_base_map():
    assert _mapbox_style_to_base_map("open-street-map") == "open-street-map"
    assert _mapbox_style_to_base_map("streets") == "open-street-map"
    assert _mapbox_style_to_base_map("carto-positron") == "carto-positron"
    assert _mapbox_style_to_base_map("dark") == "dark"
    assert _mapbox_style_to_base_map("satellite") == "dark"
    assert _mapbox_style_to_base_map("white-bg") == "white"
    assert _mapbox_style_to_base_map("unknown-style") == "open-street-map"


def test_process_colormap_values_normalized():
    values = {"id1": {"v": 0.2}, "id2": {"v": 0.4}}
    value_dict, cmin, cmax = _process_colormap_values(values, "Jet")
    assert cmin == pytest.approx(0.2)
    assert cmax == pytest.approx(0.4)
    assert value_dict["id1"] == pytest.approx(0.0)
    assert value_dict["id2"] == pytest.approx(1.0)


def test_process_colormap_values_fixed_scale():
    values = {"id1": {"v": 0.2}}
    value_dict, cmin, cmax = _process_colormap_values(values, "fixed_line_rating_scale")
    assert value_dict["id1"] == pytest.approx(0.2)
    assert cmin == pytest.approx(0.2)
    assert cmax == pytest.approx(0.2)


def test_process_colormap_values_not_dict_raises():
    with pytest.raises(ValueError, match="Expected cmap_vals to be a dictionary"):
        _process_colormap_values(["id1"], "Jet")


def test_process_colormap_values_bad_inner_dict_raises():
    with pytest.raises(ValueError, match="Expected inner_dict"):
        _process_colormap_values({"id1": {"v": 0.2, "w": 0.4}}, "Jet")


def test_process_colormap_values_cmax_too_large_raises():
    with pytest.raises(ValueError, match="cannot be greater than 1.0"):
        _process_colormap_values({"id1": {"v": 1.2}}, "Jet")


def test_get_colormap_color_fixed_scale():
    assert _get_colormap_color(0.0, "fixed_line_rating_scale") == "#0000ff"
    assert _get_colormap_color(1.0, "fixed_line_rating_scale") == "#ff0000"


def test_get_colormap_color_is_clamped():
    assert _get_colormap_color(-0.5, "Jet") == _get_colormap_color(0.0, "Jet")
    assert _get_colormap_color(1.5, "Jet") == _get_colormap_color(1.0, "Jet")


def test_get_colormap_color_named_colormap():
    color = _get_colormap_color(0.5, "Jet")
    assert color.startswith("#")
    assert len(color) == 7


def test_get_lons_lats():
    lons, lats = _get_lons_lats(
        '{"type": "LineString", "coordinates": [[8.5, 47.0], [8.6, 47.1]]}'
    )
    assert lons == (8.5, 8.6)
    assert lats == (47.0, 47.1)
