from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional, Union

import numpy as np
import pandas as pd
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
    cmap_lines: Optional[str] = None,
    cmap_line_values: Optional[Union[list, dict]] = None,
    cbar_line_title: Optional[str] = None,
    show_line_colorbar: bool = True,
    cmap_nodes: Optional[str] = None,
    cmap_node_values: Optional[Union[list, dict]] = None,
    cbar_node_title: Optional[str] = None,
    mapbox_style: Optional[str] = "open-street-map",
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
        cmap_lines (Optional[str]): Name of a colormap (e.g., 'Viridis', 'Jet', 'Blues', etc.) used for the lines
        cmap_line_values (Optional[Union[list, dict]]): Values for colormap line trace. Can be a list of values
                                                 or dict mapping line IDs to values.
        cbar_line_title (Optional[str]): Title for the line colorbar.
        show_line_colorbar (bool): Whether to show the colorbar for line colors. Defaults to True.
        cmap_nodes (Optional[str]): Name of a colormap (e.g., 'Viridis', 'Jet', 'Blues', etc.) used for the nodes
        cmap_node_values (Optional[Union[list, dict]]): Values for colormap node trace. Can be a list of values
                                                 or dict mapping node IDs to values.
        cbar_node_title (Optional[str]): Title for the node colorbar.
        mapbox_style (Optional[str]): Mapbox style. Defaults to open-street-map.
    Returns:
        Figure: Plotly figure.
    """
    fig = go.Figure()

    # Get disconnected lines via opened switches
    opened_switches = grid.raw_grid.switches.get_opened()

    disconnected_lines = grid.raw_grid.lines.filter_by_nodes(opened_switches.node_b)
    _, connected_lines = grid.raw_grid.lines.subset_split(disconnected_lines.uuid)

    if cmap_lines and cmap_line_values is not None:
        try:
            value_dict, cmin, cmax = _process_colormap_values(
                cmap_line_values, cmap_lines
            )
        except Exception as e:
            print(f"Error processing colormap values: {e}")

        connected_lines.data.apply(
            lambda line: _add_line_trace(
                fig,
                line,
                highlights=line_highlights,
                cmap=cmap_lines,
                value_dict=value_dict,
                cmin=cmin,
                cmax=cmax,
                cbar_title=cbar_line_title,
                show_colorbar=show_line_colorbar,
            ),
            axis=1,  # type: ignore
        )

        if show_line_colorbar is not None:
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
                            if cmap_lines == "fixed_line_rating_scale"
                            else cmap_lines
                        ),
                        cmin=(
                            cmin if not cmap_lines == "fixed_line_rating_scale" else 0.0
                        ),
                        cmax=(
                            cmax if not cmap_lines == "fixed_line_rating_scale" else 1.0
                        ),  # fixme check for values > 1.0
                        colorbar=dict(
                            title=dict(
                                text=cbar_line_title or "Line Value",
                                font=dict(size=12, weight="normal", style="normal"),
                            ),
                            x=0.975,
                            tickvals=(
                                [i / 10 for i in range(11)]
                                if cmap_lines == "fixed_line_rating_scale"
                                else None
                            ),
                            ticktext=(
                                [f"{round(i / 10.0, 2)}" for i in range(11)]
                                if cmap_lines == "fixed_line_rating_scale"
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

    if cmap_nodes and cmap_node_values is not None:
        _add_node_trace(
            fig,
            grid,
            highlights=node_highlights,
            cmap=cmap_nodes,
            cmap_node_values=cmap_node_values,
            cbar_node_title=cbar_node_title,
        )

    else:
        _add_node_trace(fig, grid, highlights=node_highlights)

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
        mapbox_style=mapbox_style,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom,  # Adjust the zoom level as per the calculated heuristic
            style=mapbox_style,
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
    value_dict: Optional[dict] = None,
    cmin: float = None,
    cmax: float = None,
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
        if cmap and value_dict and line_id in value_dict.keys():
            value = value_dict[line_id]
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
        hover_text += f"<br>{cbar_title or 'Value'}: {value:.3f}"

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
    cmap: Optional[str] = None,
    cmap_node_values: Optional[dict] = None,
    cbar_node_title: Optional[str] = None,
):
    """
    Node trace function with colormap support.

    Args:
        fig (go.Figure): The Plotly figure object.
        grid (GridContainer): The grid container holding node data.
        highlights (Optional): Highlights nodes. Defaults to None.
                               List of uuids or dict[(r, g, b), str] with colors.
        cmap (Optional[str]): Name of a colormap (e.g., 'Viridis', 'Jet', etc.).
        cmap_node_values (Optional[dict]): Dictionary mapping node IDs to values for colormap.
        cbar_node_title (Optional[str]): Title for the colorbar.

    Returns:
        Updates the given figure object with node traces and optional colorbar.
    """

    # Hover text generation
    def to_hover_text_nodes(node: pd.Series):
        hover_text = f"ID: {node.id}<br>"

        if cmap_node_values is not None:
            voltage_magnitude = cmap_node_values.get(node.name)
            if voltage_magnitude is not None:
                voltage_magnitude_str = f"{round(voltage_magnitude, 5)} pu"
                hover_text += f"Voltage Magnitude: {voltage_magnitude_str}<br>"

        hover_text += (
            f"Latitude: {node['latitude']:.6f}<br>"
            f"Longitude: {node['longitude']:.6f}"
        )

        return hover_text

    # Determine colors based on either highlights or cmap
    def _get_node_color(node_uuid):
        if highlights is not None:
            # Handle explicit highlights first
            if isinstance(highlights, dict):
                for color, nodes in highlights.items():
                    if node_uuid in nodes:
                        return rgb_to_hex(color)
            elif isinstance(highlights, list) and node_uuid in highlights:
                return rgb_to_hex(RED)  # Default highlight color is red

        # Handle colormap-based coloring
        if (
            cmap is not None
            and cmap_node_values is not None
            and node_uuid in cmap_node_values.keys()
        ):
            value = cmap_node_values[node_uuid]
            # Normalize values between 0-1
            normalized_value = (value - cmin) / (cmax - cmin) if cmax != cmin else 0.5
            return _get_colormap_color(normalized_value, cmap)

        return rgb_to_hex(BLUE)

    nodes_data = grid.raw_grid.nodes.data

    if cmap and cmap_node_values is not None:
        cmin = 0.9
        cmax = 1.1

        # Create a custom colorscale for the colorbar
        custom_colorscale = px.colors.get_colorscale(cmap)
        # Add a separate trace for colorbar
        fig.add_trace(
            go.Scattermapbox(
                mode="markers",
                lon=[nodes_data["longitude"].mean()],
                lat=[nodes_data["latitude"].mean()],
                marker=dict(
                    size=0.1,
                    opacity=0,
                    colorscale=custom_colorscale,
                    cmin=0.9,
                    cmax=1.1,
                    colorbar=dict(
                        title=dict(
                            text=cbar_node_title or "Node Value", font=dict(size=12)
                        ),
                        x=1.025,
                        tickvals=(
                            [
                                0.9 + i * 2 / 100 for i in range(11)
                            ]  # FIXME maybe the upper and lower value is not at the max / min pos -> see lines...
                        ),
                        ticktext=([f"{round(0.9 + i*2 / 100, 2)}" for i in range(11)]),
                        thickness=10,
                        tickfont=dict(size=12, weight="normal", style="normal"),
                    ),
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    hover_texts = nodes_data.apply(
        lambda node_data: to_hover_text_nodes(node_data), axis=1
    )

    node_colors = {}
    for _, node_data in nodes_data.iterrows():
        node_colors[node_data.name] = _get_node_color(node_data.name)

    # Create a color list based on the ID column in nodes_data
    color_list = []
    for node_uuid in nodes_data.index:
        color = node_colors.get(
            node_uuid, rgb_to_hex(BLUE)
        )  # Default to blue if no color found
        color_list.append(color)

    fig.add_trace(
        go.Scattermapbox(
            mode="markers",
            lon=nodes_data["longitude"],
            lat=nodes_data["latitude"],
            hovertext=hover_texts,
            hoverinfo="text",
            marker=dict(size=8, color=color_list),
            showlegend=False,
        )
    )


def _get_lons_lats(geojson: str):
    """Extract longitude and latitude coordinates from GeoJSON string."""
    coordinates = json.loads(geojson)["coordinates"]
    return list(zip(*coordinates))  # returns lons, lats
