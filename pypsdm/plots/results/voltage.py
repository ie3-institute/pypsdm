import math
from datetime import datetime
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.ts.base import EntityKey
from pypsdm.models.ts.mixins import ComplexVoltageDictMixin
from pypsdm.models.ts.types import (
    ComplexVoltage,
    ComplexVoltageDict,
    ComplexVoltagePowerDict,
)
from pypsdm.plots.common.line_plot import ax_plot_time_series
from pypsdm.plots.common.utils import (
    FIGSIZE,
    LABEL_PAD,
    Resolution,
    set_subplot_title,
    set_suptitle,
    set_title,
    set_xlabels_rotated,
    set_ylabel,
)


def plot_all_v_mag_branch_violin(
    nodes_res: ComplexVoltageDictMixin,
    branches: list[list[str]],
    title: str | None = None,
    **kwargs,
):
    """
    Plots violin plots for all nodes across all branches.
    Branches of the grid can be retrieved by raw_grid.get_branches()

    Args:
        gwr: GridWithResults object

    Returns:
        fig, axes
    """
    width, height = FIGSIZE
    height = height * len(branches)
    fig, axes = plt.subplots(nrows=len(branches), figsize=(width, height))
    for i, branch in enumerate(branches):
        axs = axes[i] if len(branches) > 1 else axes
        ax_plot_v_mags_violin(axs, nodes_res, branch, **kwargs)  # type: ignore
        if len(branches) > 1:
            set_subplot_title(axs, f"Voltages along Branch {i+1}")

    if not title:
        title = "Voltage Magnitudes along Branches"
    set_suptitle(fig, title)
    plt.tight_layout()
    plt.grid(True)

    return fig, axes


def plot_v_mags_violin(
    nodes_res: ComplexVoltageDict,
    nodes: list[str] | None = None,
    title: str | None = None,
    **kwargs,
):
    """
    Plots violin plots for all given nodes .

    Args:
        nodes_res: NodesResult or ExtendedNodesResult object
        nodes: Optional list of node uuids that should be plotted. Order is preserved.

    Returns:
        fig, ax
    """
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_v_mags_violin(ax, nodes_res, nodes, **kwargs)

    if not title:
        title = "Voltage Magnitudes"
    set_title(ax, title)
    return fig, ax


def ax_plot_v_mags_violin(
    ax: Axes,
    nodes_res: ComplexVoltageDict,
    nodes: Optional[list[str]],  # branches can be found by GridContainer.get_branches()
    **kwargs,
):
    """
    Plots violin plots for given nodes. If no nodes are passed all nodes are plotted.

    Args:
        ax: Axes object
        nodes_res: NodesResult or ExtendedNodesResult object
        nodes: Optional list of node uuids that should be plotted. Order is preserved.
    """

    if nodes:
        # get v_mag in listed sequence
        v_mag = nodes_res.subset(nodes).v_mag(favor_ids=False).reindex(columns=nodes)
        uuid_id_map = {k.uuid: k.id for k in nodes_res.keys()}
        v_mag.columns = [uuid_id_map[col] for col in v_mag.columns]
    else:
        v_mag = nodes_res.v_mag()

    data = []
    for col in v_mag.columns:
        data.append(v_mag[col].dropna().values)

    ax.violinplot(data, **kwargs)

    # set labels
    x_labels = v_mag.columns
    set_xlabels_rotated(ax, list(x_labels), ha="right")
    set_ylabel(ax, "Voltage magnitude in pu")
    _ = ax.set_xticklabels(x_labels, rotation=45, ha="right")


def plot_v_mag_branch(
    nodes_res: ComplexVoltageDict,
    branch: list[str],  # branches can be found by GridContainer.get_branches()
    time: datetime,
    in_kw: bool = False,
):
    """
    Plots voltage magnitudes of nodes along the given branch.

    Args:
        nodes_res: NodesResult or ExtendedNodesResult object
        branch: list of node uuids that form the branch
        time: datetime for which the voltage magnitudes should be plotted
        in_kw: if True, power is plotted in kW instead of MW

    Returns:
        fig, ax
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    ax_plot_v_mag_branch(ax, nodes_res, branch, time, fig=fig, in_kw=in_kw)
    set_title(ax, "Voltage Magnitudes along Branch")
    return fig, ax


def ax_plot_v_mag_branch(
    ax: Axes,
    nodes_res: ComplexVoltageDict,
    branch: list[str],
    time: datetime,
    fig: Optional[Figure] = None,  # used to plot colorbar
    in_kw: bool = False,
):
    """
    Plots voltage magnitudes of nodes along the given branch.

    Args:
        ax: Axes object
        nodes_res: NodesResult or ExtendedNodesResult object
        branch: list of node uuids that form the branch
        time: datetime for which the voltage magnitudes should be plotted
        fig: Optional Figure object which is used to plot the colorbar
        in_kw: if True, power is plotted in kW instead of MW
    """

    with_power = isinstance(nodes_res, ComplexVoltagePowerDict)

    v_mags = []
    x_ticks = []
    p_s = []

    for node in branch:
        node_res = nodes_res[node]
        res = node_res[time]
        v_mag = res.v_mag.iloc[0]

        # happens for auxiliary node at open switch
        if math.isnan(v_mag):  # type: ignore
            continue
        v_mags.append(v_mag)

        if with_power:
            p_s.append(res.p.iloc[0])  # type: ignore
        x_ticks.append(node_res.name)  # type: ignore

    ax.plot(x_ticks, v_mags)
    ax.set_xticks(np.arange(len(x_ticks)))  # xtick locations
    ax.set_xticklabels(x_ticks, rotation=45, ha="right")  # set xtick labels
    set_ylabel(ax, "Voltage Magnitude in p.u.")

    if with_power:
        # plot aggregated node power indicator
        cmap = sns.color_palette("coolwarm", as_cmap=True)
        if in_kw:
            p_s = [p * 1000 for p in p_s]
        sc = ax.scatter(x_ticks, v_mags, c=p_s, cmap=cmap, edgecolor="none", zorder=10)  # type: ignore
        if fig:
            cbar = fig.colorbar(sc, ax=ax)
            unit = "kW" if in_kw else "MW"
            cbar.set_label(f"Nodal Power in {unit}", labelpad=LABEL_PAD)


def plot_v_mag(
    res: ComplexVoltage,
    name: EntityKey | str | None = None,
    title: Optional[str] = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if title is None:
        if name:
            name = name if isinstance(name, str) else name.id
            title = f"Voltage Magnitude at Node: {name}"
        else:
            title = "Voltage Magnitude"
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_node_v_mag(
        ax,
        res,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    set_title(ax, title)
    return fig, ax


def plot_v_ang(
    res: ComplexVoltage,
    name: EntityKey | str | None = None,
    title: Optional[str] = None,
    hourly_mean: bool = False,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if title is None:
        if name:
            name = name if isinstance(name, str) else name.id
            title = f"Voltage Magnitude at Node: {name}"
        else:
            title = "Voltage Magnitude"
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_node_v_ang(
        ax,
        res,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    set_title(ax, title)
    return fig, ax


def ax_plot_node_v_mag(
    ax: Axes,
    res: ComplexVoltage,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if len(res.v_mag) == 0:
        raise ValueError("Voltage magnitude time series is empty. No data to plot")

    ax = ax_plot_time_series(
        ax,
        res.v_mag,
        entity_type=RawGridElementsEnum.NODE,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Voltage Magnitude in p.u.")


def ax_plot_node_v_ang(
    ax: Axes,
    res: ComplexVoltage,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if len(res.v_ang) == 0:
        raise ValueError("Voltage angle time series is empty. No data to plot")

    ax = ax_plot_time_series(
        ax,
        res.v_ang,
        entity_type=RawGridElementsEnum.NODE,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Voltage Angle in deg")
