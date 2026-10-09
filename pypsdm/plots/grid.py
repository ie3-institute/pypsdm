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

from pypsdm.plots.common.utils import (
    BLUE,
    GREEN,
    GREY,
    OVERLOAD_COLOR,
    RED,
    RGB,
    rgb_to_hex,
)


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
    line_color: Optional[str] = None,
) -> go.Figure:
    """
    Plots the grid on an OpenStreetMap. Supports Line and Node highlighting as well as colored map for line traces. Lines that are disconnected due to open switches will be grey.

    When using ``cmap_lines="fixed_line_rating_scale"`` with values above 1.0
    (e.g. line utilisation where the current exceeds ``i_max``), the
    overloaded lines are highlighted with a dedicated magenta color.

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
        line_color (Optional[str]): Base color (hex string) for the line traces that are
            not part of the line colormap. Defaults to green.
    Returns:
        Figure: Plotly figure.
    """
    fig = go.Figure()

    # Get disconnected lines via opened switches
    opened_switches = grid.raw_grid.switches.get_opened()

    disconnected_lines = grid.raw_grid.lines.filter_by_nodes(opened_switches.node_b)
    _, connected_lines = grid.raw_grid.lines.subset_split(disconnected_lines.uuid)

    both_color_bars = (
        show_line_colorbar and cmap_lines is not None and cmap_nodes is not None
    )

    if (show_line_colorbar and cmap_lines is not None) or cmap_nodes is not None:
        # Plot white half transparent rectangle as background for color bars
        x0_value = 0.85 if both_color_bars else 0.925
        fig.add_shape(
            type="rect",
            x0=x0_value,
            x1=1.0,
            y0=0.0,
            y1=1.0,
            fillcolor="rgba(255, 255, 255, 0.5)",
            line=dict(color="rgba(255, 255, 255, 0.0)"),
        )

    if cmap_lines and cmap_line_values is not None:
        try:
            value_dict, cmin, cmax, overloaded, raw_value_dict = (
                _process_colormap_values(cmap_line_values, cmap_lines)
            )
        except Exception as e:
            print(f"Error processing colormap values: {e}")
            value_dict, cmin, cmax, overloaded, raw_value_dict = (
                None,
                0.0,
                1.0,
                {},
                None,
            )

        connected_lines.data.apply(
            lambda line: _add_line_trace(
                fig,
                line,
                highlights=line_highlights,
                cmap=cmap_lines,
                value_dict=value_dict,
                raw_value_dict=raw_value_dict,
                overloaded=overloaded,
                cbar_title=cbar_line_title,
                show_colorbar=show_line_colorbar,
                line_color=line_color,
            ),
            axis=1,  # type: ignore
        )

        if show_line_colorbar:
            custom_colorscale = [
                [i / 10, f"rgb({int(255 * (i / 10))},0,{int(255 * (1 - i / 10))})"]
                for i in range(11)
            ]
            lons, lats = _get_lons_lats(grid.lines.geo_position.iloc[0])

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
                        ),
                        colorbar=dict(
                            title=dict(
                                text=cbar_line_title or "Line Value",
                                font=dict(
                                    size=12,
                                    weight="normal",
                                    style="normal",
                                    color="#000000",
                                ),
                            ),
                            x=x0_value,
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
                            len=0.85,
                            tickfont=dict(
                                size=12,
                                weight="normal",
                                style="normal",
                                color="#000000",
                            ),
                        ),
                        showscale=True,
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
    else:
        connected_lines.data.apply(
            lambda line: _add_line_trace(fig, line, is_disconnected=False, highlights=line_highlights, line_color=line_color), axis=1  # type: ignore
        )

    disconnected_lines.data.apply(
        lambda line: _add_line_trace(
            fig,
            line,
            is_disconnected=True,
            highlights=line_highlights,
            highlight_disconnected=highlight_disconnected,
            line_color=line_color,
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


def _process_colormap_values(
    cmap_vals: dict, cmap
) -> tuple[dict, float, float, dict, dict]:
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
        raw_dict = {uuid: float(value) for uuid, value in zip(uuids, values)}

        return normalized_dict, cmin, cmax, {}, raw_dict
    else:
        # Values must be in the 0-1 range on the fixed scale.
        # Lines exceeding 1.0 (i.e. current above i_max) are treated
        # as overloaded and highlighted with a dedicated color.
        overloaded = {
            uuid: float(value) for uuid, value in zip(uuids, values) if value > 1.0
        }
        value_dict = {uuid: value for uuid, value in zip(uuids, values)}
        return value_dict, cmin, cmax, overloaded, value_dict


def _get_colormap_color(value, cmap):
    """Get color from colormap based on a normalized value in the 0-1 range.

    The color is interpolated between the surrounding stops of the colorscale
    so that it matches the continuously interpolated colorbar.
    """
    value = min(max(value, 0), 1)

    if cmap == "fixed_line_rating_scale":
        # Use Fixed Scale
        colorscale = []
        scale_segments = 10

        for i in range(scale_segments + 1):
            # Calculate the interpolation factor
            factor = i / scale_segments

            # Interpolate RGB values
            r = int(255 * factor)  # Red increases from 0 to 255
            g = 0  # Green remains at 0
            b = int(255 * (1 - factor))  # Blue decreases from 255 to 0

            colorscale.append([factor, f"rgb({r}, {g}, {b})"])
    else:
        # Use Plotly's colorscale
        colorscale = px.colors.get_colorscale(cmap)

    # Interpolate between the two surrounding stops of the scale
    if value <= colorscale[0][0]:
        rgb_values = _parse_color(colorscale[0][1])
    elif value >= colorscale[-1][0]:
        rgb_values = _parse_color(colorscale[-1][1])
    else:
        rgb_values = None
        for (pos0, color0), (pos1, color1) in zip(colorscale, colorscale[1:]):
            if pos0 <= value <= pos1:
                if pos1 == pos0:
                    rgb_values = _parse_color(color0)
                else:
                    t = (value - pos0) / (pos1 - pos0)
                    rgb0 = _parse_color(color0)
                    rgb1 = _parse_color(color1)
                    rgb_values = [
                        int(round(rgb0[i] + (rgb1[i] - rgb0[i]) * t)) for i in range(3)
                    ]
                break

    hex_string = "#%02x%02x%02x" % (
        int(rgb_values[0]),
        int(rgb_values[1]),
        int(rgb_values[2]),
    )
    return hex_string


def _parse_color(color_str):
    """Parse a plotly color (rgb string or hex string) into a list of (r, g, b) values."""
    color_str = color_str.strip()
    if color_str.startswith("rgb("):
        return list(map(int, color_str[4:-1].replace(" ", "").split(",")))
    hex_color = color_str.lstrip("#")
    return [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]


def _with_alpha(color: str, alpha: float) -> str:
    """Convert a plotly color to an rgba string with the given alpha (0.0 - 1.0)."""
    r, g, b = _parse_color(color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _add_line_trace(
    fig: go.Figure,
    line_data: Series,
    is_disconnected: bool = False,
    highlights: Optional[Union[dict[tuple, str], list[str]]] = None,
    highlight_disconnected: Optional[bool] = False,
    cmap: Optional[str] = None,
    value_dict: Optional[dict] = None,
    raw_value_dict: Optional[dict] = None,
    overloaded: Optional[dict] = None,
    cbar_title: Optional[str] = None,
    show_colorbar: bool = True,
    line_color: Optional[str] = None,
):
    """Enhanced line trace function with colormap support."""
    lons, lats = _get_lons_lats(line_data.geo_position)
    hover_text = line_data["id"]

    line_color = line_color or rgb_to_hex(GREEN)
    highlighted = False

    colormap_value = None

    line_id = line_data.name if hasattr(line_data, "name") else line_data["id"]
    if not is_disconnected:
        if cmap and value_dict and line_id in value_dict.keys():
            value = value_dict[line_id]
            if (
                cmap == "fixed_line_rating_scale"
                and overloaded
                and line_id in overloaded
            ):
                colormap_value = rgb_to_hex(OVERLOAD_COLOR)
                use_colorbar = True
            else:
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
        # Show the original (un-normalized) value in the hover text
        hover_value = raw_value_dict[line_id] if raw_value_dict else value
        hover_text += f"<br>{cbar_title or 'Value'}: {hover_value:.3f}"

    # Add the lines with or without colorbar
    line_color_to_use = (
        colormap_value
        if colormap_value is not None and use_colorbar and show_colorbar is not None
        else line_color
    )

    fig.add_trace(
        go.Scattermapbox(
            mode="lines",
            lon=lons,
            lat=lats,
            hoverinfo="skip",  # Skip hoverinfo for the lines
            line=dict(color=line_color_to_use, width=2),
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
                lon=[nodes_data["longitude"][0]],
                lat=[nodes_data["latitude"][0]],
                marker=dict(
                    size=0.1,
                    opacity=0,
                    colorscale=custom_colorscale,
                    cmin=0.9,
                    cmax=1.1,
                    colorbar=dict(
                        title=dict(
                            text=cbar_node_title or "Node Value",
                            font=dict(size=12, color="#000000"),
                        ),
                        x=0.925,
                        tickvals=([0.9 + i * 2 / 100 for i in range(11)]),
                        ticktext=([f"{round(0.9 + i*2 / 100, 2)}" for i in range(11)]),
                        thickness=10,
                        len=0.85,
                        tickfont=dict(
                            size=12, weight="normal", style="normal", color="#000000"
                        ),
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


def _add_soil_layer_trace(
    fig: go.Figure,
    soil_layers: pd.DataFrame,
    soil_types: Optional[pd.DataFrame] = None,
    depth: float = 0.0,
    opacity: float = 0.4,
) -> None:
    """
    Draws the soil layer polygons that are present at a given depth on top of
    the figure. Each area (polygon) gets an individual color from a qualitative
    palette so that the different areas can be differentiated easily.

    Args:
        fig (go.Figure): The Plotly figure object to draw on.
        soil_layers (pd.DataFrame): Soil layers as loaded from ``soilLayers.csv``.
            Expected columns are ``uuid``, ``geometry`` (GeoJSON string),
            ``z_from``, ``z_to`` and ``soil_type``.
        soil_types (Optional[pd.DataFrame]): Soil types as loaded from
            ``soilTypes.csv`` to enrich the hover text.
        depth (float): Depth in m (negative values below the surface, e.g. -0.8).
            Only layers with ``z_from >= depth >= z_to`` are shown.
        opacity (float): Fill opacity of the polygons. Defaults to 0.4.
    """
    if soil_layers.empty:
        return

    # Only keep the layers that cover the requested depth
    # (z_from is closer to the surface, z_to is deeper, both negative or 0)
    mask = (soil_layers["z_from"] >= depth) & (soil_layers["z_to"] <= depth)
    layers = soil_layers.loc[mask]
    if layers.empty:
        return

    soil_type_names = {}
    if soil_types is not None and len(soil_types) > 0:
        # Column names may contain whitespace (e.g. " id"), normalize them
        soil_types = soil_types.rename(columns=str.strip)
        if "id" in soil_types.columns:
            soil_type_names = {
                str(uuid).strip(): str(name).strip()
                for uuid, name in zip(soil_types["uuid"], soil_types["id"])
            }

    distinct_colors = px.colors.qualitative.Set2

    for color_idx, (_, layer) in enumerate(layers.iterrows()):
        color = distinct_colors[color_idx % len(distinct_colors)]
        # The geometry is a GeoJSON polygon: coordinates[0] is the outer ring
        coordinates = json.loads(layer["geometry"])["coordinates"][0]
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]

        soil_type = layer.get("soil_type")
        soil_type_name = soil_type_names.get(str(soil_type).strip(), soil_type)
        hover_text = (
            f"Soil Layer: {layer['uuid']}<br>"
            f"Soil Type: {soil_type_name}<br>"
            f"Depth Range: {layer['z_from']:.2f} m to {layer['z_to']:.2f} m"
        )

        fig.add_trace(
            go.Scattermapbox(
                mode="lines",
                lon=lons,
                lat=lats,
                fill="toself",
                fillcolor=_with_alpha(color, opacity),
                line=dict(color=_with_alpha(color, min(1.0, opacity + 0.3)), width=1),
                hoverinfo="text",
                hovertext=hover_text,
                showlegend=False,
            )
        )


def thermal_line_segment_plot(
    grid: GridContainer,
    segments: pd.DataFrame,
    segment_values: Optional[dict] = None,
    cmap: Optional[str] = "Jet",
    cbar_title: Optional[str] = None,
    show_colorbar: bool = True,
    mapbox_style: Optional[str] = "open-street-map",
    line_width: int = 4,
    value_range: Optional[tuple[float, float]] = None,
    soil_layers: Optional[pd.DataFrame] = None,
    soil_types: Optional[pd.DataFrame] = None,
    soil_depth: Optional[float] = None,
    soil_opacity: float = 0.4,
) -> go.Figure:
    """
    Plots the thermal line segments (created during an ampacity simulation)
    on top of the grid. Each segment is a sub-part of a line with its own
    thermal state.

    Optionally, the soil layer areas that are present at a given depth
    (e.g. the cable burial depth) can be drawn on top of the segments.
    Each area is filled with an individual color so that the different areas
    can be differentiated easily.

    Args:
        grid (GridContainer): Grid to plot.
        segments (pd.DataFrame): Thermal line segments as loaded from
            ``thermal_line_segments.csv``. Expected columns are
            ``segmentUuid``, ``lineUuid``, ``startX``, ``startY``, ``endX``,
            ``endY`` and (optionally) ``limitTemperature``.
        segment_values (Optional[dict]): Dictionary mapping segment UUIDs to
            values (e.g. segment temperature in °C) used for the colormap.
            Without values, each segment gets an individual color from a
            qualitative palette so that the segments can be differentiated.
        cmap (Optional[str]): Name of a colormap (e.g. 'Jet', 'Viridis', etc.).
        cbar_title (Optional[str]): Title for the colorbar.
        show_colorbar (bool): Whether to show the colorbar. Defaults to True.
        mapbox_style (Optional[str]): Mapbox style. Defaults to open-street-map.
        line_width (int): Line width for the segment traces. Defaults to 4.
        value_range (Optional[tuple[float, float]]): Fixed (min, max) range of
            the colormap scale. If None, the range is derived from the values
            themselves. Use a fixed range (e.g. (0, 100) for temperatures in
            °C) if the colors should stay comparable between different
            timestamps.
        soil_layers (Optional[pd.DataFrame]): Soil layers as loaded from
            ``soilLayers.csv``. If given together with ``soil_depth``, the
            layer areas that are present at that depth are drawn on the map.
        soil_types (Optional[pd.DataFrame]): Soil types as loaded from
            ``soilTypes.csv`` to enrich the hover text of the soil layers.
        soil_depth (Optional[float]): Depth in m (negative values below the
            surface, e.g. -0.8) at which the soil layer areas are shown.
        soil_opacity (float): Fill opacity of the soil layer polygons.
            Defaults to 0.4.
    Returns:
        Figure: Plotly figure.
    """
    fig = grid_plot(
        grid,
        mapbox_style=mapbox_style,
        show_line_colorbar=False,
        line_color="#000000",
    )

    # Draw the soil layer areas first so that the segments are on top
    if soil_layers is not None and soil_depth is not None:
        _add_soil_layer_trace(
            fig,
            soil_layers,
            soil_types=soil_types,
            depth=soil_depth,
            opacity=soil_opacity,
        )

    if segments.empty:
        return fig

    cmin, cmax = 0.0, 1.0
    if segment_values:
        values = pd.Series(segment_values)
        cmin, cmax = float(values.min()), float(values.max())
        # Avoid a degenerated colorbar (single value) - expand the range
        # slightly so that the colors still match the colorbar
        if cmin == cmax:
            cmin, cmax = cmin - 1.0, cmax + 1.0
        if value_range is not None:
            cmin, cmax = value_range

    limit_temperature_column = (
        "limitTemperature" if "limitTemperature" in segments.columns else None
    )

    # Without values, sample an individual color per segment from a qualitative
    # palette so that the segments can be visually differentiated
    distinct_colors = px.colors.qualitative.Plotly

    for color_idx, (_, seg) in enumerate(segments.iterrows()):
        value = segment_values.get(seg["segmentUuid"]) if segment_values else None
        if value is not None:
            norm = (value - cmin) / (cmax - cmin) if cmax != cmin else 0.5
            color = _get_colormap_color(norm, cmap)
        else:
            color = distinct_colors[color_idx % len(distinct_colors)]

        hover_text = f"Segment: {seg['segmentUuid']}<br>Line: {seg['lineUuid']}"
        if value is not None:
            hover_text += f"<br>{cbar_title or 'Value'}: {value:.4f}"
        if limit_temperature_column is not None:
            hover_text += f"<br>Limit Temperature: {seg['limitTemperature']} °C"

        fig.add_trace(
            go.Scattermapbox(
                mode="lines",
                lon=[seg["startX"], seg["endX"]],
                lat=[seg["startY"], seg["endY"]],
                line=dict(color=color, width=line_width),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        # Add a transparent marker at the midpoint of the segment for the hover text
        mid_lon = (seg["startX"] + seg["endX"]) / 2
        mid_lat = (seg["startY"] + seg["endY"]) / 2
        fig.add_trace(
            go.Scattermapbox(
                mode="markers",
                lon=[mid_lon],
                lat=[mid_lat],
                hoverinfo="text",
                hovertext=hover_text,
                marker=dict(size=0, opacity=0, color=color),
                showlegend=False,
            )
        )

    if segment_values and show_colorbar:
        first = segments.iloc[0]
        fig.add_trace(
            go.Scattermapbox(
                mode="markers",
                lon=[first["startX"]],
                lat=[first["startY"]],
                marker=dict(
                    size=0.1,
                    opacity=0,
                    color="#008000",
                    colorscale=px.colors.get_colorscale(cmap),
                    cmin=cmin,
                    cmax=cmax,
                    colorbar=dict(
                        title=dict(
                            text=cbar_title or "Segment Value",
                            side="right",
                            font=dict(
                                size=12,
                                weight="normal",
                                style="normal",
                                color="#000000",
                            ),
                        ),
                        x=0.925,
                        y=0.5,
                        yanchor="middle",
                        thickness=15,
                        len=0.85,
                        tickfont=dict(
                            size=12, weight="normal", style="normal", color="#000000"
                        ),
                    ),
                    showscale=True,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    return fig
