from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from pypsdm.models.gwr import GridWithResults
from pypsdm.models.result.grid.connector import ConnectorResult
from pypsdm.models.result.grid.transformer import Transformer2WResult
from pypsdm.plots.common.line_plot import ax_plot_time_series
from pypsdm.plots.common.utils import (
    BLUE,
    FIGSIZE,
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
