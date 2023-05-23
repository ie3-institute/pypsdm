import json

import plotly.graph_objs as go
from pandas import Series
from shapely.geometry import LineString

from psdm_analysis.models.input.container.grid_container import GridContainer
from psdm_analysis.plots.common.utils import BLUE, GREY, RED, rgb_to_hex


def get_lons_lats(geojson: str):
    coordinates = json.loads(geojson)["coordinates"]
    return list(zip(*coordinates))  # returns lons, lats


def grid_plot(grid: GridContainer):
    """
    Plots the grid on an OpenStreetMap. Lines that are disconnected due to open switches will be grey.

    ATTENTION:
    We currently consider the node_b of the switches to be the auxiliary switch node.
    This is not enforced within the PSDM so might not work as expected.
    If that is the case the wrong lines might be grey.
    """
    fig = go.Figure()

    # Get disconnected lines via opened switches
    opened_switches = grid.raw_grid.switches.get_opened()

    disconnected_lines = grid.raw_grid.lines.find_lines_by_nodes(opened_switches.node_b)
    _, connected_lines = grid.raw_grid.lines.subset_split(disconnected_lines.uuids)

    connected_lines.data.apply(lambda line: add_line_trace(fig, line), axis=1)
    disconnected_lines.data.apply(
        lambda line: add_line_trace(fig, line, is_disconnected=True), axis=1
    )

    add_node_trace(fig, grid)

    center_lat = grid.raw_grid.nodes.data["latitude"].mean()
    center_lon = grid.raw_grid.nodes.data["longitude"].mean()

    # Dynamically calculate the zoom level
    lat_range = (
        grid.raw_grid.nodes.data["latitude"].max()
        - grid.raw_grid.nodes.data["latitude"].min()
    )
    lon_range = (
        grid.raw_grid.nodes.data["longitude"].max()
        - grid.raw_grid.nodes.data["longitude"].min()
    )

    zoom = 12 - max(lat_range, lon_range)

    fig.update_layout(
        # mapbox = {"zoom"=10},
        showlegend=False,
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom,  # Adjust the zoom level as per the calculated heuristic
            style="open-street-map",
        ),
    )

    return fig


def add_line_trace(fig: go.Figure, line_data: Series, is_disconnected: bool = False):
    lons, lats = get_lons_lats(line_data.geo_position)
    hover_text = line_data["id"]

    color = GREY if is_disconnected else RED

    # Add the lines
    fig.add_trace(
        go.Scattermapbox(
            mode="lines",
            lon=lons,
            lat=lats,
            hoverinfo="skip",  # Skip hoverinfo for the lines
            line=dict(color=rgb_to_hex(color)),
        ),
    )

    # Create a LineString object from the line's coordinates
    line = LineString(zip(lons, lats))

    # Calculate the midpoint on the line based on distance
    midpoint = line.interpolate(line.length / 2)

    # Add a transparent marker at the midpoint of the line for hover text
    fig.add_trace(
        go.Scattermapbox(
            mode="markers",
            lon=[midpoint.x],
            lat=[midpoint.y],
            hoverinfo="text",
            hovertext=hover_text,
            marker=dict(size=0, opacity=0, color=rgb_to_hex(RED)),
        )
    )


def add_node_trace(fig: go.Figure, grid: GridContainer):
    node_hover_data = grid.get_nodal_sp_count_and_power()
    nodes_data = grid.raw_grid.nodes.data

    def to_hover_text(node_data: Series):
        return (
            node_data["id"]
            + "<br>"
            + "<br>".join(
                [
                    f"{key}={value}"
                    for key, value in node_hover_data[node_data.name].items()
                ]
            )
        )

    text = nodes_data.apply(
        lambda node_data: to_hover_text(node_data), axis=1
    ).to_list()

    fig.add_trace(
        go.Scattermapbox(
            mode="markers",
            lon=nodes_data["longitude"],
            lat=nodes_data["latitude"],
            hovertext=text,
            hoverinfo="text",
            marker=dict(size=6, color=rgb_to_hex(BLUE)),
            text=text,
        )
    )
