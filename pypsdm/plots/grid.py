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
    use_mapbox: bool = True,  # New parameter to control mapbox vs regular scatter
    zoom_box: Optional[dict] = None,  # New parameter for zoom box
    show_axes: bool = True,  # New parameter to control axis visibility
) -> go.Figure:
    """
    Unified grid plotting function that supports both mapbox and SVG-friendly modes.

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
        use_mapbox (bool): Whether to use mapbox (True) or regular scatter plots (False).
                          When False, creates SVG-friendly plots. Defaults to True.
        zoom_box (Optional[dict]): Dictionary with keys 'lat_min', 'lat_max', 'lon_min', 'lon_max'
                                  to zoom to a specific bounding box. If None, auto-fits to grid data.
        show_axes (bool): Whether to show axis labels, ticks, and grid (only for non-mapbox).
                         Defaults to True.
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

    # Add colorbar background if needed
    if (show_line_colorbar and cmap_lines is not None) or cmap_nodes is not None:
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

    # Process lines with colormap
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
                cbar_title=cbar_line_title,
                show_colorbar=show_line_colorbar,
                use_mapbox=use_mapbox,
            ),
            axis=1,  # type: ignore
        )

        if show_line_colorbar:
            _add_line_colorbar(
                fig, grid, cmap_lines, cmin, cmax, cbar_line_title, x0_value, use_mapbox
            )
    else:
        connected_lines.data.apply(
            lambda line: _add_line_trace(
                fig,
                line,
                is_disconnected=False,
                highlights=line_highlights,
                use_mapbox=use_mapbox,
            ),
            axis=1,
        )

    # Add disconnected lines
    disconnected_lines.data.apply(
        lambda line: _add_line_trace(
            fig,
            line,
            is_disconnected=True,
            highlights=line_highlights,
            highlight_disconnected=highlight_disconnected,
            use_mapbox=use_mapbox,
        ),
        axis=1,
    )

    # Add nodes
    if cmap_nodes and cmap_node_values is not None:
        _add_node_trace(
            fig,
            grid,
            highlights=node_highlights,
            cmap=cmap_nodes,
            cmap_node_values=cmap_node_values,
            cbar_node_title=cbar_node_title,
            use_mapbox=use_mapbox,
        )
    else:
        _add_node_trace(fig, grid, highlights=node_highlights, use_mapbox=use_mapbox)

    # Configure layout
    _configure_layout(fig, grid, use_mapbox, mapbox_style, zoom_box, show_axes)

    return fig


def _process_colormap_values(cmap_vals: dict, cmap) -> tuple[dict, float, float]:
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

    if cmax > 1.0:
        raise ValueError(f"Error: cmax ({cmax}) cannot be greater than 1.0.")

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
        scale_segments = 10

        for i in range(scale_segments + 1):
            # Calculate the interpolation factor
            factor = i / scale_segments

            # Interpolate RGB values
            r = int(255 * factor)  # Red increases from 0 to 255
            g = 0  # Green remains at 0
            b = int(255 * (1 - factor))  # Blue decreases from 255 to 0

            rgb_color = f"rgb({r}, {g}, {b})"
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

    # Convert to hex
    rgb_values = list(map(int, rgb_string[4:-1].split(",")))
    hex_string = "#%02x%02x%02x" % tuple(rgb_values)
    return hex_string


def _add_line_trace(
    fig: go.Figure,
    line_data: Series,
    is_disconnected: bool = False,
    highlights: Optional[Union[dict[tuple, str], list[str]]] = None,
    highlight_disconnected: Optional[bool] = False,
    cmap: Optional[str] = None,
    value_dict: Optional[dict] = None,
    cbar_title: Optional[str] = None,
    show_colorbar: bool = True,
    use_mapbox: bool = True,
):
    """Unified line trace function supporting both mapbox and regular scatter."""
    lons, lats = _get_lons_lats(line_data.geo_position)
    hover_text = line_data["id"]

    line_color = rgb_to_hex(GREEN)
    highlighted = False

    colormap_value = None

    line_id = line_data.name if hasattr(line_data, "name") else line_data["id"]

    # Determine color
    if not is_disconnected:
        if cmap and value_dict and line_id in value_dict.keys():
            value = value_dict[line_id]
            colormap_value = _get_colormap_color(value, cmap)
            hover_text += f"<br>{cbar_title or 'Value'}: {value:.3f}"
        else:
            colormap_value = "#008000"

    # Check for highlights (overrides colormap)
    if isinstance(highlights, dict):
        for color, lines in highlights.items():
            if line_data.name in lines:
                line_color = rgb_to_hex(color)
                highlighted = True
    elif highlights is not None:
        if line_data.name in highlights:
            line_color = rgb_to_hex(RED)
            highlighted = True

    # Handle disconnected lines
    if (highlight_disconnected is False) and is_disconnected:
        if not highlighted:
            line_color = rgb_to_hex(GREY)

    # Use colormap color if not highlighted
    if cmap and colormap_value is not None and not highlighted:
        line_color = colormap_value

    # Add the lines with or without colorbar
    line_color_to_use = (
        colormap_value
        if colormap_value is not None and show_colorbar is not None
        else line_color
    )

    fig.add_trace(
        go.Scattermapbox(
            mode="lines",
            lon=lons,
            lat=lats,
            hoverinfo="skip",
            line=dict(color=line_color_to_use, width=2),
            showlegend=False,
        )
    )
    # Add hover point at midpoint
    line = LineString(zip(lons, lats))
    midpoint = line.interpolate(line.length / 2)
    fig.add_trace(
        go.Scattermapbox(
            mode="markers",
            lon=[midpoint.x],
            lat=[midpoint.y],
            hoverinfo="text",
            hovertext=hover_text,
            marker=dict(size=0, opacity=0, color=line_color_to_use),
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
    use_mapbox: bool = True,
):
    """Unified node trace function supporting both mapbox and regular scatter."""

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

    def _get_node_color(node_uuid):
        if highlights is not None:
            # Handle explicit highlights first
            if isinstance(highlights, dict):
                for color, nodes in highlights.items():
                    if node_uuid in nodes:
                        return rgb_to_hex(color)
            elif isinstance(highlights, list) and node_uuid in highlights:
                return rgb_to_hex(RED)  # Default highlight color is red

        if (
            cmap is not None
            and cmap_node_values is not None
            and node_uuid in cmap_node_values.keys()
        ):
            value = cmap_node_values[node_uuid]
            cmin, cmax = 0.9, 1.1  # Fixed range for nodes
            normalized_value = (value - cmin) / (cmax - cmin) if cmax != cmin else 0.5
            return _get_colormap_color(normalized_value, cmap)

        return rgb_to_hex(BLUE)

    nodes_data = grid.raw_grid.nodes.data

    # Add colorbar if needed
    if cmap and cmap_node_values is not None:
        _add_node_colorbar(fig, nodes_data, cmap, cbar_node_title, use_mapbox)

    hover_texts = nodes_data.apply(
        lambda node_data: to_hover_text_nodes(node_data), axis=1
    )

    color_list = []
    for node_uuid in nodes_data.index:
        color = _get_node_color(node_uuid)
        color_list.append(color)

    # Add the node trace
    if use_mapbox:
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
    else:
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=nodes_data["longitude"],
                y=nodes_data["latitude"],
                hovertext=hover_texts,
                hoverinfo="text",
                marker=dict(size=8, color=color_list),
                showlegend=False,
            )
        )


def _add_line_colorbar(
    fig, grid, cmap_lines, cmin, cmax, cbar_line_title, x0_value, use_mapbox
):
    """Add line colorbar for both mapbox and regular plots."""
    custom_colorscale = [
        [i / 10, f"rgb({int(255 * (i / 10))},0,{int(255 * (1 - i / 10))})"]
        for i in range(11)
    ]

    colorbar_config = dict(
        title=dict(
            text=cbar_line_title or "Line Value",
            font=dict(size=12, color="#000000"),
        ),
        x=x0_value,
        thickness=15,
        len=0.85,
        tickfont=dict(size=12, color="#000000"),
    )

    # Add tick configuration for fixed scale
    if cmap_lines == "fixed_line_rating_scale":
        colorbar_config.update(
            {
                "tickvals": [i / 10 for i in range(11)],
                "ticktext": [f"{round(i / 10.0, 2)}" for i in range(11)],
            }
        )

    marker_config = dict(
        size=0.1,
        opacity=0,
        color="#008000",
        colorscale=(
            custom_colorscale if cmap_lines == "fixed_line_rating_scale" else cmap_lines
        ),
        cmin=(cmin if cmap_lines != "fixed_line_rating_scale" else 0.0),
        cmax=(cmax if cmap_lines != "fixed_line_rating_scale" else 1.0),
        colorbar=colorbar_config,
        showscale=True,
    )

    if use_mapbox:
        lons, lats = _get_lons_lats(grid.lines.geo_position.iloc[0])
        fig.add_trace(
            go.Scattermapbox(
                mode="markers",
                lon=[lons[0]],
                lat=[lats[0]],
                marker=marker_config,
                hoverinfo="skip",
                showlegend=False,
            )
        )
    else:
        nodes_data = grid.raw_grid.nodes.data
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=[nodes_data["longitude"].mean()],
                y=[nodes_data["latitude"].mean()],
                marker=marker_config,
                hoverinfo="skip",
                showlegend=False,
            )
        )


def _add_node_colorbar(fig, nodes_data, cmap, cbar_node_title, use_mapbox):
    """Add node colorbar for both mapbox and regular plots."""
    custom_colorscale = px.colors.get_colorscale(cmap)

    colorbar_config = dict(
        title=dict(
            text=cbar_node_title or "Node Value",
            font=dict(size=12, color="#000000"),
        ),
        x=0.925,
        thickness=10,
        len=0.85,
        tickvals=[0.9 + i * 2 / 100 for i in range(11)],
        ticktext=[f"{round(0.9 + i * 2 / 100, 2)}" for i in range(11)],
        tickfont=dict(size=12, color="#000000"),
    )

    marker_config = dict(
        size=0.1,
        opacity=0,
        colorscale=custom_colorscale,
        cmin=0.9,
        cmax=1.1,
        colorbar=colorbar_config,
    )

    if use_mapbox:
        fig.add_trace(
            go.Scattermapbox(
                mode="markers",
                lon=[nodes_data["longitude"].mean()],
                lat=[nodes_data["latitude"].mean()],
                marker=marker_config,
                hoverinfo="skip",
                showlegend=False,
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=[nodes_data["longitude"].mean()],
                y=[nodes_data["latitude"].mean()],
                marker=marker_config,
                hoverinfo="skip",
                showlegend=False,
            )
        )


def _configure_layout(fig, grid, use_mapbox, mapbox_style, zoom_box, show_axes):
    """Configure the figure layout based on mapbox usage and zoom settings."""
    # Determine zoom/extent settings
    if zoom_box is not None:
        lat_min, lat_max = zoom_box["lat_min"], zoom_box["lat_max"]
        lon_min, lon_max = zoom_box["lon_min"], zoom_box["lon_max"]
        center_lat = (lat_min + lat_max) / 2
        center_lon = (lon_min + lon_max) / 2
        lat_range = lat_max - lat_min
        lon_range = lon_max - lon_min
    else:
        lat_min = grid.raw_grid.nodes.data["latitude"].min()
        lat_max = grid.raw_grid.nodes.data["latitude"].max()
        lon_min = grid.raw_grid.nodes.data["longitude"].min()
        lon_max = grid.raw_grid.nodes.data["longitude"].max()
        center_lat = grid.raw_grid.nodes.data["latitude"].mean()
        center_lon = grid.raw_grid.nodes.data["longitude"].mean()
        lat_range = lat_max - lat_min
        lon_range = lon_max - lon_min

    if use_mapbox:
        # Mapbox layout
        zoom = (
            14.5 - max(lat_range, lon_range)
            if zoom_box
            else 12 - max(lat_range, lon_range)
        )
        fig.update_layout(
            showlegend=False,
            mapbox_style=mapbox_style,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            mapbox=dict(
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom,
                style=mapbox_style,
            ),
        )
    else:
        # Regular scatter plot layout
        padding_lat = lat_range * 0.05 if lat_range > 0 else 0.001
        padding_lon = lon_range * 0.05 if lon_range > 0 else 0.001

        if show_axes:
            xaxis_config = dict(
                title="Longitude",
                showgrid=True,
                gridcolor="lightgray",
                gridwidth=0.5,
                range=[lon_min - padding_lon, lon_max + padding_lon],
                showline=True,
                linecolor="black",
                linewidth=1,
                ticks="outside",
                showticklabels=True,
            )
            yaxis_config = dict(
                title="Latitude",
                showgrid=True,
                gridcolor="lightgray",
                gridwidth=0.5,
                scaleanchor="x",
                scaleratio=1,
                range=[lat_min - padding_lat, lat_max + padding_lat],
                showline=True,
                linecolor="black",
                linewidth=1,
                ticks="outside",
                showticklabels=True,
            )
        else:
            xaxis_config = dict(
                title="",
                showgrid=False,
                range=[lon_min - padding_lon, lon_max + padding_lon],
                showline=False,
                ticks="",
                showticklabels=False,
                zeroline=False,
            )
            yaxis_config = dict(
                title="",
                showgrid=False,
                scaleanchor="x",
                scaleratio=1,
                range=[lat_min - padding_lat, lat_max + padding_lat],
                showline=False,
                ticks="",
                showticklabels=False,
                zeroline=False,
            )

        fig.update_layout(
            showlegend=False,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            xaxis=xaxis_config,
            yaxis=yaxis_config,
            plot_bgcolor="white",
        )


def _get_lons_lats(geojson: str):
    """Extract longitude and latitude coordinates from GeoJSON string."""
    coordinates = json.loads(geojson)["coordinates"]
    return list(zip(*coordinates))  # returns lons, lats


def create_zoom_box(
    upper_left_lat: float,
    upper_left_lon: float,
    bottom_right_lat: float,
    bottom_right_lon: float,
) -> dict:
    """
    Create a zoom box dictionary from center coordinates and span.

    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        lat_span: Total latitude span (degrees)
        lon_span: Total longitude span (degrees)

    Returns:
        Dictionary with lat_min, lat_max, lon_min, lon_max keys
    """
    return {
        "lat_min": bottom_right_lat,
        "lat_max": upper_left_lat,
        "lon_min": upper_left_lon,
        "lon_max": bottom_right_lon,
    }
