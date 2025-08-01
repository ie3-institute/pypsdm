from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Union

import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from pandas import Series
from shapely.geometry import LineString

if TYPE_CHECKING:
    from pypsdm.models.input.container.grid import GridContainer

from pypsdm.plots.common.utils import BLUE, GREEN, GREY, RED, RGB, rgb_to_hex


def grid_plot(
    grid: GridContainer,
    node_highlights: Optional[Union[dict[RGB, list[str]], list[str]]] = None,
    line_highlights: Optional[Union[dict[RGB, list[str]], list[str]]] = None,
    highlight_disconnected: Optional[bool] = False,
    cmap: Optional[str] = None,
    cmap_line_values: Optional[Union[list, dict]] = None,
    cbar_title: Optional[str] = None,
    show_colorbar: bool = True,
) -> go.Figure:
    """
    Plots the grid on an OpenStreetMap. Supports Line and Node highlighting as well as colored map for line traces. Lines that are disconnected due to open switches will be grey.

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
        highlight_disconnected (Optional[bool]): Whether to highlight disconnected lines.
        cmap (Optional[str]): Name of a colormap (e.g., 'Viridis', 'Jet', 'Blues', etc.)
        cmap_line_values (Optional[Union[list, dict]]): Values for colormap. Can be a list of values
                                                 or dict mapping line IDs to values.
        cbar_title (Optional[str]): Title for the colorbar.
        show_colorbar (bool): Whether to show the colorbar.
    Returns:
        Figure: Plotly figure.
    """
    fig = go.Figure()

    # Get disconnected lines via opened switches
    opened_switches = grid.raw_grid.switches.get_opened()

    disconnected_lines = grid.raw_grid.lines.filter_by_nodes(opened_switches.node_b)
    _, connected_lines = grid.raw_grid.lines.subset_split(disconnected_lines.uuid)

    if cmap and cmap_line_values is not None:
        try:
            value_dict, cmin, cmax = _process_colormap_values(cmap_line_values, cmap)
        except Exception as e:
            print(f"Error processing colormap values: {e}")

        connected_lines.data.apply(
            lambda line: _add_line_trace(
                fig,
                line,
                highlights=line_highlights,
                cmap=cmap,
                colormap_value_dict=value_dict,
                line_data_dict=cmap_line_values,
                cbar_title=cbar_title,
                show_colorbar=show_colorbar,
            ),
            axis=1,  # type: ignore
        )

        if show_colorbar is not None:
            custom_colorscale = [
                [i / 10, f"rgb({int(255 * (i / 10))},0,{int(255 * (1 - i / 10))})"]
                for i in range(11)
            ]
            lons, lats = _get_lons_lats(grid.lines.geo_position.iloc[0])

            fig.add_shape(
                type="rect",
                x0=0.95,
                x1=1.00,
                y0=0.0,
                y1=1.0,
                fillcolor="white",
                line=dict(color="white"),
            )

            # Add a separate trace for line colorbar (using a single point)
            fig.add_trace(
                go.Scattermapbox(
                    mode="markers",
                    lon=[lons[0]],
                    lat=[lats[0]],
                    marker=dict(
                        size=0.1,
                        opacity=0,
                        color="#008000",
                        colorscale=(
                            custom_colorscale
                            if cmap == "fixed_line_rating_scale"
                            else cmap
                        ),
                        cmin=(cmin if not cmap == "fixed_line_rating_scale" else 0.0),
                        cmax=(
                            cmax if not cmap == "fixed_line_rating_scale" else 1.0
                        ),  # fixme check for values > 1.0
                        colorbar=dict(
                            title=dict(
                                text=cbar_title or "Line Value",
                                font=dict(size=12, weight="normal", style="normal"),
                            ),
                            x=0.975,
                            tickvals=(
                                [i / 10 for i in range(11)]
                                if cmap == "fixed_line_rating_scale"
                                else None
                            ),
                            ticktext=(
                                [f"{round(i / 10.0, 2)}" for i in range(11)]
                                if cmap == "fixed_line_rating_scale"
                                else None
                            ),
                            thickness=15,
                            tickfont=dict(size=12, weight="normal", style="normal"),
                        ),
                        showscale=True,
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
    else:
        connected_lines.data.apply(
            lambda line: _add_line_trace(fig, line, is_disconnected=False, highlights=line_highlights), axis=1  # type: ignore
        )

    disconnected_lines.data.apply(
        lambda line: _add_line_trace(
            fig,
            line,
            is_disconnected=True,
            highlights=line_highlights,
            highlight_disconnected=highlight_disconnected,
        ),  # type: ignore
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


def _process_colormap_values(cmap_vals: dict, cmap) -> (dict, float, float):
    """Process colormap values and return a dictionary with original values in case of fixed scale or one with normalized data."""
    values = []
    uuids = []

    if isinstance(cmap_vals, dict):
        for uuid, inner_dict in cmap_vals.items():
            if isinstance(inner_dict, dict) and len(inner_dict) == 1:
                # Extract the first (and only) value from each inner dict
                value = list(inner_dict.values())[0]
                values.append(value)
                uuids.append(uuid)
            else:
                raise ValueError(
                    f"Expected inner_dict for {uuid} to be a dictionary with one item."
                )
    else:
        raise ValueError("Expected cmap_vals to be a dictionary.")

    values = np.array(values)

    cmin = np.min(values)
    cmax = np.max(values)

    if cmap != "fixed_line_rating_scale":
        # Normalize values to 0-1 range
        normalized_values = (
            (values - cmin) / (cmax - cmin) if cmax != cmin else np.zeros_like(values)
        )
        normalized_dict = {
            uuid: norm_value for uuid, norm_value in zip(uuids, normalized_values)
        }

        return normalized_dict, cmin, cmax
    else:
        value_dict = {uuid: value for uuid, value in zip(uuids, values)}
        return value_dict, cmin, cmax


def _get_colormap_color(value, cmap):
    """Get color from colormap based on value."""
    value = min(max(value, 0), 1)

    if cmap == "fixed_line_rating_scale":
        # Use Fixed Scale
        colorscale = []
        for i in range(11):
            # Calculate the interpolation factor
            factor = i / (11 - 1)

            # Interpolate RGB values
            r = int(255 * factor)  # Red increases from 0 to 255
            g = 0  # Green remains at 0
            b = int(255 * (1 - factor))  # Blue decreases from 255 to 0

            rgb_color = f"rgb({r},{g},{b})"
            colorscale.append([factor, rgb_color])
        index = int(
            value * (len(colorscale) - 1)
        )  # This gives us an index between 0 and len(colorscale)-1
        rgb_string = colorscale[index][1]  # Get the corresponding RGB color
    else:
        # Use Plotly's colorscale to get the color
        colorscale = px.colors.get_colorscale(cmap)
        index = int(value * (len(colorscale) - 1))

        color_str = colorscale[index]
        rgb_string = color_str[1]
    # Remove 'rgb(' and ')' and split by commas
    rgb_values = list(map(int, rgb_string[4:-1].split(",")))
    hex_string = "#%02x%02x%02x" % (
        int(rgb_values[0]),
        int(rgb_values[1]),
        int(rgb_values[2]),
    )
    return hex_string


def _add_line_trace(
    fig: go.Figure,
    line_data: Series,
    is_disconnected: bool = False,
    highlights: Optional[Union[dict[tuple, str], list[str]]] = None,
    highlight_disconnected: Optional[bool] = False,
    cmap: Optional[str] = None,
    colormap_value_dict: Optional[dict] = None,
    line_data_dict: Optional[dict] = None,
    cbar_title: Optional[str] = None,
    show_colorbar: bool = True,
):
    """Enhanced line trace function with colormap support."""
    lons, lats = _get_lons_lats(line_data.geo_position)
    hover_text = line_data["id"]

    line_color = rgb_to_hex(GREEN)
    highlighted = False

    colormap_value = None

    line_id = line_data.name if hasattr(line_data, "name") else line_data["id"]
    if not is_disconnected:
        if cmap and colormap_value_dict and line_id in colormap_value_dict.keys():
            value = colormap_value_dict[line_id]
            colormap_value = _get_colormap_color(value, cmap)
            use_colorbar = True
        else:
            colormap_value = "#008000"
            use_colorbar = False

    # Check for highlights (overrides colormap)
    if isinstance(highlights, dict):
        for color, lines in highlights.items():
            if line_data.name in lines:  # type: ignore
                line_color = rgb_to_hex(color)
                highlighted = True
                use_colorbar = False
    elif highlights is not None:
        if line_data.name in highlights:
            line_color = rgb_to_hex(RED)
            highlighted = True
            use_colorbar = False

    # Handle disconnected lines
    if (highlight_disconnected is False) and is_disconnected:
        # Highlights override the disconnected status
        if not highlighted:
            line_color = rgb_to_hex(GREY)
            use_colorbar = False

    if cmap and colormap_value is not None:
        hover_text += f"<br>{cbar_title or 'Value'}: {line_data_dict[line_id][next(iter(line_data_dict[line_id]))] * 100:.1f}%"

    # Add the lines with or without colorbar
    if colormap_value is not None:
        if use_colorbar and show_colorbar is not None:
            # Add line with colorbar support
            fig.add_trace(
                go.Scattermapbox(
                    mode="lines",
                    lon=lons,
                    lat=lats,
                    hoverinfo="skip",
                    line=dict(color=colormap_value, width=2),
                    showlegend=False,
                )
            )
        else:
            # Add regular line without colorbar
            fig.add_trace(
                go.Scattermapbox(
                    mode="lines",
                    lon=lons,
                    lat=lats,
                    hoverinfo="skip",  # Skip hoverinfo for the lines
                    line=dict(color=line_color, width=2),
                    showlegend=False,
                )
            )
    else:
        # Add regular line without colormap
        fig.add_trace(
            go.Scattermapbox(
                mode="lines",
                lon=lons,
                lat=lats,
                hoverinfo="skip",  # Skip hoverinfo for the lines
                line=dict(color=line_color, width=2),
                showlegend=False,
            )
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
            marker=dict(size=0, opacity=0, color=line_color),
            showlegend=False,
        )
    )


def _add_node_trace(
    fig: go.Figure,
    grid: GridContainer,
    highlights: Optional[Union[dict[tuple, str], list[str]]] = None,
):
    """Node trace function."""
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
            + node_data.name
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
                showlegend=False,
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
    """Extract longitude and latitude coordinates from GeoJSON string."""
    coordinates = json.loads(geojson)["coordinates"]
    return list(zip(*coordinates))  # returns lons, lats
