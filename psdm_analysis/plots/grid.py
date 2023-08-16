import json
from typing import Optional, Union

import plotly.graph_objs as go
from pandas import Series
from shapely.geometry import LineString

from psdm_analysis.models.input.container.grid import GridContainer
from psdm_analysis.plots.common.utils import BLUE, GREEN, GREY, RED, rgb_to_hex


def grid_plot(
    grid: GridContainer,
    node_highlights: Optional[Union[dict[tuple, str], list[str]]] = None,
    line_highlights: Optional[Union[dict[tuple, str], list[str]]] = None,
    highlight_disconnected: Optional[bool] = False,
) -> go.Figure:
    """
    Plots the grid on an OpenStreetMap. Lines that are disconnected due to open switches will be grey.

    ATTENTION:
    We currently consider the node_b of the switches to be the auxiliary switch node.
    This is not enforced within the PSDM so might not work as expected.
    If that is the case the wrong lines might be grey.

    Args:
        grid (GridContainer): Grid to plot.
        node_highlights (Optional): Highlights nodes. Defaults to None.
                                    List of uuids or dict[(r, g, b), str] with colors.
        line_highlights (Optional): Highlights lines. Defaults to None.
                                    List of uuids or dict[(r, g, b), str] with colors.
    Returns:
        Figure: Plotly figure.
    """
    fig = go.Figure()

    # Get disconnected lines via opened switches
    opened_switches = grid.raw_grid.switches.get_opened()

    disconnected_lines = grid.raw_grid.lines.filter_by_nodes(opened_switches.node_b)
    _, connected_lines = grid.raw_grid.lines.subset_split(disconnected_lines.uuid)

    connected_lines.data.apply(
        lambda line: _add_line_trace(fig, line, highlights=line_highlights), axis=1
    )
    disconnected_lines.data.apply(
        lambda line: _add_line_trace(
            fig,
            line,
            highlights=line_highlights,
            is_disconnected=True,
            highlight_disconnected=highlight_disconnected,
        ),
        axis=1,
    )

    _add_node_trace(fig, grid, node_highlights)

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


def _add_line_trace(
    fig: go.Figure,
    line_data: Series,
    is_disconnected: bool = False,
    highlights: Optional[Union[dict[tuple, str], list[str]]] = None,
    highlight_disconnected: Optional[bool] = False,
):
    lons, lats = _get_lons_lats(line_data.geo_position)
    hover_text = line_data["id"]

    color = GREEN
    if isinstance(highlights, dict):
        for line_color, lines in highlights.items():
            if line_data.name in lines:
                color = line_color
    elif highlights is not None:
        color = RED if line_data.name in highlights else GREEN

    if (highlight_disconnected is False) and is_disconnected:
        color = GREY

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
            marker=dict(size=0, opacity=0, color=rgb_to_hex(color)),
        )
    )


def _add_node_trace(
    fig: go.Figure,
    grid: GridContainer,
    highlights: Optional[Union[dict[tuple, str], list[str]]] = None,
):
    node_hover_data = grid.get_nodal_sp_count_and_power()
    nodes_data = grid.raw_grid.nodes.data

    def to_hover_text(node_data: Series):
        if node_data.name not in node_hover_data:
            raise ValueError(
                f"Node with uuid: {node_data.name} not found in node_hover_data"
            )

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

    def _node_trace(data, color):
        text = data.apply(lambda node_data: to_hover_text(node_data), axis=1).to_list()

        fig.add_trace(
            go.Scattermapbox(
                mode="markers",
                lon=data["longitude"],
                lat=data["latitude"],
                hovertext=text,
                hoverinfo="text",
                marker=dict(size=6, color=rgb_to_hex(color)),
                text=text,
            )
        )

    if highlights is not None:
        if isinstance(highlights, dict):
            rmd = []
            for nodes in highlights.values():
                rmd.extend(nodes)
            rmd = nodes_data.drop(rmd)
            _node_trace(rmd, BLUE)

            # plot highlighted nodes second so they are on top
            for color, nodes in highlights.items():
                highlighted_nodes = nodes_data.loc[nodes]
                _node_trace(highlighted_nodes, color)
        elif isinstance(highlights, list):
            rmd = nodes_data.drop(highlights)
            _node_trace(rmd, BLUE)

            # plot highlighted nodes second so they are on top
            highlighted_nodes = nodes_data.loc[highlights]
            _node_trace(highlighted_nodes, RED)
        else:
            raise ValueError(
                "Invalid type for highlights. We expect a list of ids or a dict of colors and ids."
            )
    else:
        _node_trace(nodes_data, BLUE)


def _get_lons_lats(geojson: str):
    coordinates = json.loads(geojson)["coordinates"]
    return list(zip(*coordinates))  # returns lons, lats
