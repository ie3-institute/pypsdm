import logging
from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from pypsdm.models.gwr import GridWithResults
from pypsdm.models.input.connector.lines import Lines
from pypsdm.models.result.grid.connector import ConnectorResult
from pypsdm.models.result.grid.transformer import Transformer2WResult
from pypsdm.plots.common.line_plot import ax_plot_time_series
from pypsdm.plots.common.utils import (
    BLUE,
    FIGSIZE,
    ax_plot_secondary_axis,
    set_subplot_title,
    set_suptitle,
    set_title,
)


def plot_transformer_s(
    res: Transformer2WResult,
    side: str,
    gwr: GridWithResults,
    resolution: str,
    include_utilisation: bool = True,
    show_util_grid_lines: bool = False,
    title: Optional[str] = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    transformer_name = res.name if res.name else res.input_model
    if title is None:
        title = f"Rated Power Transformer: {transformer_name}"
    if include_utilisation:
        width, height = FIGSIZE
        fig, axs = plt.subplots(2, 1, figsize=(width, height * 2), sharex=False)
        ax_plot_transformer_s(
            axs[0],
            res,
            side,
            gwr,
            resolution,
            fill_from_index=fill_from_index,
            fill_between=fill_between,
            set_x_label=set_x_label,
            **kwargs,
        )
        set_subplot_title(axs[0], "Rated Power Magnitude")
        ax_plot_transformer_utilization(
            axs[1],
            res,
            side,
            gwr,
            resolution,
            fill_from_index=fill_from_index,
            fill_between=fill_between,
            set_x_label=False,
            color=BLUE,
            **kwargs,
        )
        set_subplot_title(axs[1], "Transformer Utilization")
        fig.suptitle(title, fontsize=16)
        fig.subplots_adjust(hspace=0.4)
        return fig, axs
    else:
        fig, ax = plt.subplots(figsize=FIGSIZE)
        ax_plot_transformer_s(
            ax,
            res,
            side,
            gwr,
            resolution,
            fill_from_index=fill_from_index,
            fill_between=fill_between,
            set_x_label=set_x_label,
            **kwargs,
        )
        set_suptitle(fig, title)
        return fig, ax


def ax_plot_transformer_s(
    ax: Axes,
    res: Transformer2WResult,
    side: str,
    gwr: GridWithResults,
    resolution: str,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    if len(res.i_a_mag) == 0:
        raise ValueError("Transformer current time series is empty. No data to plot")

    rated_power = res.calc_apparent_power_gwr(gwr, side).apply(lambda x: np.real(x))
    ax_plot_time_series(
        ax,
        rated_power,
        res.entity_type,
        resolution,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )
    ax.set_ylabel("Rated Power in kVA")


def ax_plot_transformer_utilization(
    ax: Axes,
    res: Transformer2WResult,
    side: str,
    gwr: GridWithResults,
    resolution: str,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    ax_plot_time_series(
        ax,
        res.calc_transformer_utilisation(gwr, side),
        res.entity_type,
        resolution,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )
    ax.set_ylabel("Transformer Utilization")


def plot_line_current(
    res: ConnectorResult,
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
    res: ConnectorResult,
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
            logging.warning("No i_max_src provided. Cannot plot utilisation")
            return
        if isinstance(i_max_src, float) or isinstance(i_max_src, int):
            line_i_max = i_max_src
        elif isinstance(i_max_src, Lines):
            line_i_max = i_max_src.subset(res.input_model).i_max.iloc[0]
        else:
            raise ValueError(
                f"i_max_src should be either float or Lines, got {type(i_max_src)}"
            )
        utilisation = current / line_i_max
        ax_plot_secondary_axis(
            ax, utilisation, "Line Utilisation", show_secondary_grid_lines=True
        )


def plot_connector_current(
    res: ConnectorResult,
    side: str,
    resolution: str,
    title: Optional[str] = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    connector_type = res.entity_type.get_plot_name()
    connector_name = res.name if res.name else res.input_model
    if title is None:
        title = f"Current Magnitude {connector_type}: {connector_name}"
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_connector_current(
        ax,
        res,
        side,
        resolution,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )
    ax.set_ylabel("Current in Ampere")
    set_title(ax, title)
    return fig, ax


def ax_plot_connector_current(
    ax: Axes,
    res: ConnectorResult,
    side: str,
    resolution: str,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    connector_type = res.entity_type.get_plot_name()
    if len(res.i_a_mag) == 0:
        raise ValueError(
            f"{connector_type} current time series is empty. No data to plot"
        )

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


def ax_plot_connector_angle(
    ax: Axes,
    res: ConnectorResult,
    side: str,
    resolution: str,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    connector_type = res.entity_type.get_plot_name()
    if len(res.i_a_mag) == 0:
        raise ValueError(
            f"{connector_type} angle time series is empty. No data to plot"
        )

    angle = get_connector_angle(side, res)

    ax = ax_plot_time_series(
        ax,
        angle,
        res.entity_type,
        resolution,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )


def get_connector_current(side: str, res: ConnectorResult):
    if side == "a":
        return res.i_a_mag
    elif side == "b":
        return res.i_b_mag
    else:
        raise ValueError('Side should be either "a" for node a or "b" for node b')


def get_connector_angle(side: str, res: ConnectorResult):
    if side == "a":
        return res.i_a_ang
    elif side == "b":
        return res.i_b_ang
    else:
        raise ValueError('Side should be either "a" for node a or "b" for node b')
