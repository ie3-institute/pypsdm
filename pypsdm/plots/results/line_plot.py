from typing import Optional, Union

import matplotlib.pyplot as plt
from loguru import logger
from matplotlib.axes import Axes

from pypsdm.models.input.connector.lines import Lines
from pypsdm.models.result.grid.line import LineResult
from pypsdm.plots.common.line_plot import ax_plot_time_series
from pypsdm.plots.common.utils import FIGSIZE, ax_plot_secondary_axis, set_title
from pypsdm.plots.results.connector_plot import get_connector_current


def plot_line_current(
    res: LineResult,
    side: str,
    resolution: str,
    include_utilisation: bool = False,
    i_max_src: Optional[Union[float, Lines]] = None,
    title: Optional[str] = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    line_name = res.name if res.name else res.input_model
    if title is None:
        title = f"Current Magnitude Line: {line_name}"
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_line_current(
        ax,
        res,
        side,
        resolution,
        i_max_src=i_max_src,
        include_utilisation=include_utilisation,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )
    ax.set_ylabel("Current in Ampere")
    set_title(ax, title)
    return fig, ax


def ax_plot_line_current(
    ax: Axes,
    res: LineResult,
    side: str,
    resolution: str,
    include_utilisation: bool = True,
    i_max_src: Optional[Union[float, Lines]] = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    if len(res.i_a_mag) == 0:
        raise ValueError("Line current time series is empty. No data to plot")

    current = get_connector_current(side, res)

    ax = ax_plot_time_series(
        ax,
        current,
        res.entity_type,
        resolution,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )
    ax.set_ylabel("Current Magnitude in Ampere")

    if include_utilisation:
        if i_max_src is None:
            logger.warning("No i_max_src provided. Cannot plot utilisation")
            return
        utilisation = res.utilisation(i_max_src)
        ax_plot_secondary_axis(
            ax, utilisation, "Line Utilisation", show_secondary_grid_lines=True
        )
