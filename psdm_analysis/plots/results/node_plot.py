from typing import Optional

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.axes import Axes

from psdm_analysis.models.result.grid.node import NodeResult
from psdm_analysis.plots.common.line_plot import ax_plot_time_series
from psdm_analysis.plots.common.utils import FIGSIZE, set_title

sns.set_style("whitegrid")


def plot_v_mag(
    res: NodeResult,
    resolution: str,
    title: Optional[str] = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    if title is None:
        title = f"Voltage Magnitude at Node: {res.name}"
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_node_v_mag(
        ax,
        res,
        resolution,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )
    set_title(ax, title)
    return fig, ax


def plot_v_ang(
    res: NodeResult,
    resolution: str,
    title: Optional[str] = None,
    hourly_mean: bool = False,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    if title is None:
        title = f"Voltage Angle at Node: {res.name}"
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_node_v_ang(
        ax,
        res,
        resolution,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )
    set_title(ax, title)
    return fig, ax


def ax_plot_node_v_mag(
    ax: Axes,
    res: NodeResult,
    resolution: str,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    if len(res.v_mag) == 0:
        raise ValueError("Voltage magnitude time series is empty. No data to plot")

    ax = ax_plot_time_series(
        ax,
        res.v_mag,
        res.type,
        resolution,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )
    ax.set_ylabel("Voltage Magnitude in p.u.")


def ax_plot_node_v_ang(
    ax: Axes,
    res: NodeResult,
    resolution: str,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    **kwargs,
):
    if len(res.v_ang) == 0:
        raise ValueError("Voltage angle time series is empty. No data to plot")

    ax = ax_plot_time_series(
        ax,
        res.v_ang,
        res.type,
        resolution,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        **kwargs,
    )
    ax.set_ylabel("Voltage Angle in deg")
