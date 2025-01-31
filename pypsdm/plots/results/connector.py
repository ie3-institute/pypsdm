from typing import Literal, Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from pypsdm.models.enums import EntitiesEnum, RawGridElementsEnum
from pypsdm.models.gwr import GridWithResults
from pypsdm.models.result.grid.connector import ConnectorCurrent
from pypsdm.models.result.grid.transformer import Transformer2WResult
from pypsdm.models.ts.base import EntityKey
from pypsdm.plots.common.line_plot import ax_plot_time_series
from pypsdm.plots.common.utils import (
    BLUE,
    FIGSIZE,
    Resolution,
    set_subplot_title,
    set_suptitle,
    set_title,
)


def plot_transformer_s(
    trafo_key: str | EntityKey,
    res: Transformer2WResult,
    gwr: GridWithResults,
    side: Literal["hv", "lv"] = "hv",
    include_utilisation: bool = True,
    title: Optional[str] = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if isinstance(trafo_key, EntityKey):
        name = trafo_key.id
    else:
        name = trafo_key
    title = f"Rated Power Transformer: {name}"
    if include_utilisation:
        width, height = FIGSIZE
        fig, axs = plt.subplots(2, 1, figsize=(width, height * 2), sharex=False)
        ax_plot_transformer_s(
            axs[0],
            trafo_key,
            res,
            gwr,
            side=side,
            fill_from_index=fill_from_index,
            fill_between=fill_between,
            set_x_label=set_x_label,
            resolution=resolution,
            **kwargs,
        )
        set_subplot_title(axs[0], "Rated Power Magnitude")
        ax_plot_transformer_utilization(
            axs[1],
            trafo_key,
            res,
            gwr,
            side=side,
            fill_from_index=fill_from_index,
            fill_between=fill_between,
            set_x_label=False,
            color=BLUE,
            resolution=resolution,
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
            trafo_key,
            res,
            gwr,
            sides=side,
            fill_from_index=fill_from_index,
            fill_between=fill_between,
            set_x_label=set_x_label,
            resolution=resolution,
            **kwargs,
        )
        set_suptitle(fig, title)
        return fig, ax


def ax_plot_transformer_s(
    ax: Axes,
    trafo_key: str | EntityKey,
    res: Transformer2WResult,
    gwr: GridWithResults,
    side: Literal["hv", "lv"],
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if len(res.data) == 0:
        raise ValueError("Transformer current time series is empty. No data to plot")

    rated_power = res.apparent_power(trafo_key, gwr, side).apply(lambda x: np.real(x))
    ax_plot_time_series(
        ax,
        rated_power,
        entity_type=RawGridElementsEnum.TRANSFORMER_2_W,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Rated Power in kVA")


def ax_plot_transformer_utilization(
    ax: Axes,
    trafo_key: str | EntityKey,
    res: Transformer2WResult,
    gwr: GridWithResults,
    side: Literal["hv", "lv"] = "hv",
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    ax_plot_time_series(
        ax,
        res.utilisation(trafo_key, gwr, side),
        entity_type=RawGridElementsEnum.TRANSFORMER_2_W,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Transformer Utilization")


def plot_connector_current(
    res: ConnectorCurrent,
    key: str | EntityKey | None = None,
    side: Literal["a", "b"] = "a",
    title: Optional[str] = None,
    entity_type: EntitiesEnum | None = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if title is None:
        if key is not None:
            title = (
                f"Current Magnitude: {key.id if isinstance(key, EntityKey) else key}"
            )
        else:
            title = "Current Magnitude"
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_connector_current(
        ax,
        res,
        side=side,
        entity_type=entity_type,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Current in Ampere")
    set_title(ax, title)
    return fig, ax


def ax_plot_connector_current(
    ax: Axes,
    res: ConnectorCurrent,
    side: Literal["a", "b"] = "a",
    entity_type: EntitiesEnum | None = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if len(res.i_a_mag) == 0:
        raise ValueError("Connector current time series is empty. No data to plot")

    current = get_connector_current(side, res)

    ax = ax_plot_time_series(
        ax,
        current,
        entity_type=entity_type,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Current Magnitude in Ampere")


def ax_plot_connector_angle(
    ax: Axes,
    res: ConnectorCurrent,
    side: Literal["a", "b"] = "a",
    entity_type: EntitiesEnum | None = None,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if len(res.i_a_mag) == 0:
        raise ValueError("Angle time series is empty. No data to plot")

    angle = get_connector_angle(side, res)

    ax = ax_plot_time_series(
        ax,
        angle,
        entity_type=entity_type,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )


def get_connector_current(side: Literal["a", "b"], res: ConnectorCurrent):
    if side == "a":
        return res.i_a_mag
    elif side == "b":
        return res.i_b_mag
    else:
        raise ValueError('Side should be either "a" for node a or "b" for node b')


def get_connector_angle(side: str, res: ConnectorCurrent):
    if side == "a":
        return res.i_a_ang
    elif side == "b":
        return res.i_b_ang
    else:
        raise ValueError('Side should be either "a" for node a or "b" for node b')
