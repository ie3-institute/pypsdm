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
    cmap_vals: Optional[Union[list, dict]] = None,
    cbar_title: Optional[str] = None,
    show_colorbar: bool = True,
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
        highlight_disconnected (Optional[bool]): Whether to highlight disconnected lines.
        cmap (Optional[str]): Name of a colormap (e.g., 'Viridis', 'Jet', 'Blues', etc.)
        cmap_vals (Optional[Union[list, dict]]): Values for colormap. Can be a list of values
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

    # Process colormap values if provided
    colormap_data = None
    if cmap and cmap_vals is not None:
        try:
            colormap_data = _process_colormap_values(cmap_vals)
        except Exception as e:
            print(f"Error processing colormap values: {e}")

    connected_lines.data.apply(
        lambda line: _add_line_trace(
            fig,
            line,
            highlights=line_highlights,
            cmap=cmap,
            colormap_data=colormap_data,
            cbar_title=cbar_title,
            show_colorbar=show_colorbar,
        ),
        axis=1,  # type: ignore
    )

    disconnected_lines.data.apply(
        lambda line: _add_line_trace(
            fig,
            line,
            highlights=line_highlights,
            is_disconnected=True,
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


def _process_colormap_values(cmap_vals: dict) -> dict:
    """Process colormap values and return normalized data."""
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

    # Normalize values to 0-1 range
    normalized_values = (
        (values - cmin) / (cmax - cmin) if cmax != cmin else np.zeros_like(values)
    )

    return {
        "values": values,
        "normalized": normalized_values,
        "cmin": cmin,
        "cmax": cmax,
        "original_dict": {uuid: inner_dict for uuid, inner_dict in cmap_vals.items()},
    }


def _get_colormap_color(value, cmap, normalized=True):
    """Get color from colormap based on value."""
    value = min(max(value, 0), 1)

    if normalized:
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

    return "#008000"  # Default green in hex format


def _add_line_trace(
    fig: go.Figure,
    line_data: Series,
    is_disconnected: bool = False,
    highlights: Optional[Union[dict[tuple, str], list[str]]] = None,
    highlight_disconnected: Optional[bool] = False,
    cmap: Optional[str] = None,
    colormap_data: Optional[dict] = None,
    cbar_title: Optional[str] = None,
    show_colorbar: bool = True,
):
    """Enhanced line trace function with colormap support."""
    lons, lats = _get_lons_lats(line_data.geo_position)
    hover_text = line_data["id"]

    color = GREEN
    highlighted = False
    use_colorbar = False
    colormap_value = None

    # Check if we should use colormap
    if cmap and colormap_data:
        line_id = line_data.name if hasattr(line_data, "name") else line_data["id"]

        if colormap_data["original_dict"] and line_id in colormap_data["original_dict"]:
            raw_value = colormap_data["original_dict"][line_id]
            value_index = list(colormap_data["original_dict"].keys()).index(line_id)
            normalized_value = colormap_data["normalized"][value_index]
            if isinstance(raw_value, dict) and len(raw_value) == 1:
                colormap_value = list(raw_value.values())[0]
            else:
                raise ValueError(f"Colormap_value: {raw_value} causes some error")
        elif not colormap_data["original_dict"] and hasattr(line_data, "name"):
            try:
                line_index = (
                    int(line_data.name)
                    if isinstance(line_data.name, str)
                    else line_data.name
                )
                if line_index < len(colormap_data["normalized"]):
                    normalized_value = colormap_data["normalized"][line_index]
                    colormap_value = colormap_data["values"][line_index]
                else:
                    normalized_value = 0.5
                    colormap_value = None
            except (ValueError, TypeError):
                normalized_value = 0.5
                colormap_value = None
        else:
            normalized_value = 0.5
            colormap_value = None

        if colormap_value is not None:
            color = _get_colormap_color(normalized_value, cmap)
            use_colorbar = True

    # Check for highlights (overrides colormap)
    if isinstance(highlights, dict):
        for line_color, lines in highlights.items():
            if line_data.name in lines:  # type: ignore
                color = line_color
                highlighted = True
                use_colorbar = False
    elif highlights is not None:
        if line_data.name in highlights:
            color = RED
            highlighted = True
            use_colorbar = False

    # Handle disconnected lines
    if (highlight_disconnected is False) and is_disconnected:
        # Highlights override the disconnected status
        if not highlighted:
            color = GREY
            use_colorbar = False

    # Convert color to hex if it's RGB tuple
    if isinstance(color, tuple) and len(color) == 3:  # Check for RGB tuple
        line_color = rgb_to_hex(color)
    elif isinstance(color, str):
        line_color = color
        if len(color) > 7:
            raise ValueError(f"color code: {color} does not match hex format")
    else:
        line_color = rgb_to_hex(color)

    if colormap_value is not None:
        hover_text += f"<br>{cbar_title or 'Value'}: {colormap_value:.3f}"

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
                    line=dict(color=line_color, width=2),
                    showlegend=False,
                )
            )

            # Add a separate trace for colorbar (using a single point)
            fig.add_trace(
                go.Scattermapbox(
                    mode="markers",
                    lon=[lons[0]],  # Use first point
                    lat=[lats[0]],
                    marker=dict(
                        size=0.1,
                        opacity=0,
                        color=[colormap_value],
                        colorscale=cmap or "Viridis",
                        cmin=colormap_data["cmin"],
                        cmax=colormap_data["cmax"],
                        colorbar=dict(
                            title=cbar_title or "Value",
                            x=1.02,
                        ),
                        showscale=True,
                    ),
                    hoverinfo="skip",
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
    """Node trace function (unchanged from original)."""
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
