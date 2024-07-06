from typing import Union

from matplotlib import pyplot as plt

from pypsdm import GridWithResults, Transformers2W, GridResultContainer, NodesResult, GridContainer
from pypsdm.ma_thesis import get_nodes, get_lines
from pypsdm.ma_thesis.analyse import analyse_nodes, get_max_voltages, get_min_voltages, analyse_transformers2w
from pypsdm.ma_thesis.subgrid import SubGridInfo, SubGrid
from pypsdm.ma_thesis.utils import get_trafo_2w_info, hours_index
from pypsdm.models.result.container.raw_grid import Transformers2WResult
from pypsdm.plots.common.utils import *
from pypsdm.plots.grid import grid_plot


# Detection

def plot_voltage_with_congestion(
        subgrid: SubGridInfo,
        result: GridResultContainer,
        dotted: Union[float | list[float]] = None,
        width: int = 8,
        height: int = 4
):
    fig, axes = create_fig(width=width, height=height)
    congestions = hours_index(result.congestions[subgrid.sub_grid.nr].voltage) * 1

    hours_index(subgrid.node_min_max).plot(ax=axes[0])
    ax_added_dotted(axes[0], dotted)
    congestions.plot(ax=axes[1], drawstyle="steps-post")

    axes[0].set_ylabel("Spannung in pu", fontsize=11)
    format_x_axis(axes[1], len(subgrid.node_min_max.index) - 1)
    axes[1].set_yticks([0, 1])
    axes[1].set_yticklabels(["nein", "ja"], fontsize=11)
    axes[1].set_ylabel("Engpass?", fontsize=11)

    return fig


def plot_line_utilization_with_congestion(
        subgrid: SubGridInfo,
        result: GridResultContainer,
        dotted: float = 100.0,
        width: int = 8,
        height: int = 4
):
    fig, axes = create_fig(width=width, height=height)
    congestions = hours_index(result.congestions[subgrid.sub_grid.nr].line) * 1

    hours_index(subgrid.line_max * 100).plot(ax=axes[0])
    ax_added_dotted(axes[0], dotted)
    congestions.plot(ax=axes[1], drawstyle="steps-post")

    axes[0].set_ylabel("Auslastung in %", fontsize=11)
    format_x_axis(axes[1], len(subgrid.node_min_max.index) - 1)
    axes[1].set_yticks([0, 1])
    axes[1].set_yticklabels(["nein", "ja"], fontsize=11)
    axes[1].set_ylabel("Engpass?", fontsize=11)

    return fig


def plot_transformer_utilization_with_congestion(
        subgrid: SubGridInfo,
        transformer_uuids: list[str],
        gwr: GridWithResults,
        dotted: float = 100.0,
        width: int = 8,
        height: int = 4
):
    fig, axes = create_fig(width=width, height=height)
    congestions = hours_index(gwr.results.congestions[subgrid.sub_grid.nr].transformer) * 1

    transformer_max = analyse_transformers2w(transformer_uuids, gwr)

    hours_index(transformer_max * 100).plot(ax=axes[0])
    ax_added_dotted(axes[0], dotted)
    congestions.plot(ax=axes[1], drawstyle="steps-post")

    axes[0].set_ylabel("Auslastung in %", fontsize=11)
    format_x_axis(axes[1], len(subgrid.node_min_max.index) - 1)
    axes[1].set_yticks([0, 1])
    axes[1].set_yticklabels(["nein", "ja"], fontsize=11)
    axes[1].set_ylabel("Engpass?", fontsize=11)

    return fig


# Stufung

def plot_voltage_with_tapping(
        subgrid: SubGrid,
        transformer_uuids: list[str],
        results: GridResultContainer,
        dotted: Union[float | list[float]] = None,
        width: int = 8,
        height: int = 4
):
    fig, axes = create_fig(width=width, height=height)

    length = ax_plot_both_voltages(axes[0], subgrid, results.nodes, dotted)
    ax_plot_tapping(axes[1], transformer_uuids, subgrid.grid.transformers_2_w, results.transformers_2w)

    axes[0].set_ylabel("Spannung in pu", fontsize=11)
    axes[1].set_ylabel("Stufung", fontsize=11)
    format_x_axis(axes[1], length)

    return fig


# utils

def create_fig(
        nrows: int = 2,
        ncolumns: int = 1,
        sharex: bool = True,
        width: int = 8,
        height: int = 4
):
    fig, axes = plt.subplots(nrows, ncolumns, figsize=(width, height), sharex=sharex)
    # fig.tight_layout()
    return fig, axes


def format_x_axis(
    ax: Axes,
    lim: int,
    step: int = 6,
    fontsize: int = 11,
):
    if lim <= 168:
        xticks = [i for i in range(0, lim, step)]
        xticklabel = xticks
        label = "Zeit in Stunden"
    else:
        xticks = [i for i in range(0, lim, 24*7*3)]
        xticklabel = [i * 3 for i, _ in enumerate(xticks)]
        label = "Zeit in Wochen"

    ax.set_xlim(0, lim)
    ax.set_xticks(xticks)
    ax.tick_params(axis='x', which='minor', bottom=False)
    ax.set_xticklabels(xticklabel)
    ax.set_xlabel(label, fontsize=fontsize)


def ax_plot_both_voltages(
        axes: Axes,
        subgrid: SubGrid,
        results: NodesResult,
        dotted: Union[float | list[float]] = None
) -> int:
    _, node_min_max_res = analyse_nodes(subgrid.name, subgrid.grid, results)

    hours_index(node_min_max_res).plot(ax=axes)
    ax_added_dotted(axes, dotted)

    return len(node_min_max_res.index) - 1


def ax_added_dotted(
        axes: Axes,
        dotted: Union[float | list[float]] = None
):
    if dotted:
        if isinstance(dotted, float):
            axes.axhline(dotted, color="red", linestyle="--")
        else:
            [axes.axhline(dot, color="red", linestyle="--") for dot in dotted]


def ax_plot_tapping(
        axes: Axes,
        uuids: list[str],
        transformers: Transformers2W,
        result: Transformers2WResult
):
    tap_pos = pd.concat({transformers[uuid].id: result[uuid].data["tap_pos"] for uuid in uuids}, axis=1)
    hours_index(tap_pos).plot(ax=axes, drawstyle="steps-post")


# other

def plot_voltages_with_scenario(
        subgrid: SubGrid,
        results: dict[str, GridResultContainer],
        upper_limit: float = None,
        lower_limit: float = None,
        width: int = 16,
        height: int = 6
):
    fig, axes = create_fig(width=width, height=height)

    node_res = {name: res.nodes for name, res in results.items()}
    get_max_voltages(subgrid.grid, node_res).plot(ax=axes[0])
    get_min_voltages(subgrid.grid, node_res).plot(ax=axes[1])

    ax_added_dotted(axes[0], upper_limit)
    ax_added_dotted(axes[1], lower_limit)

    return fig


def plot_voltages_with_tapping(
        subgrid1: SubGridInfo,
        subgrid2: SubGridInfo,
        transformers: Transformers2W,
        transformer_res: Transformers2WResult,
        dotted: Union[float | list[float]] = None,
        width: int = 16,
        height: int = 9
):
    connectors = list(set(subgrid1.get_transformers()).intersection(subgrid2.get_transformers()))

    tap_pos = pd.concat({transformers[uuid].id: transformer_res[uuid].data["tap_pos"] for uuid in connectors}, axis=1)

    fig, axes = create_fig(nrows=3, width=width, height=height)

    subgrid1.node_min_max.plot(ax=axes[0])
    subgrid2.node_min_max.plot(ax=axes[1])
    tap_pos.plot(ax=axes[2])

    ax_added_dotted(axes[0], dotted)
    ax_added_dotted(axes[1], dotted)

    return fig


def plot_voltage_subgrid(subgrid: SubGridInfo, width: int = 16, height: int = 6):
    return subgrid.node_res.plot(figsize=(width, height), legend=False)


def plot_subgrid_with_versions(
        subgrids: dict[str, SubGridInfo],
        dotted: Union[float | list[float]] = None,
        width: int = 16,
        height: int = 6
):
    fig, axes = create_fig(nrows=len(subgrids), width=width, height=height)

    for i, key in enumerate(subgrids):
        subgrids[key].node_min_max.plot(ax=axes[i])

        ax_added_dotted(axes[i], dotted)
        axes[i].set_title(key)

    return fig


def plot_voltage_subgrids(
        subgrids: dict[int, SubGridInfo],
        dotted: Union[float | list[float]] = None,
        width: int = 16,
        height: int = 9,
        subplots: bool = True
):
    if subplots:
        fig, axes = create_fig(nrows=len(subgrids), width=width, height=height)

        for i, subgrid in enumerate(subgrids.values()):
            subgrid.node_min_max.plot(ax=axes[i])

            ax_added_dotted(axes[i], dotted)

    else:
        values = [subgrid.node_min_max for subgrid in subgrids.values()]
        fig, axes = pd.concat(values, axis=1).plot()

        ax_added_dotted(axes, dotted)

    return fig


def plot_transformer_tappings(gwr: GridWithResults, width: int = 16, height: int = 6, subplots: bool = True):
    transformers = get_trafo_2w_info(gwr)
    transformer_results = gwr.transformers_2_w_res

    res = {tr_info.id: transformer_results[uuid].data["tap_pos"] for uuid, tr_info in transformers.items()}
    res_sorted = dict(sorted(res.items()))

    tap_pos = pd.concat(res_sorted, axis=1)
    fig = tap_pos.plot(subplots=subplots, figsize=(width, height))

    fig.tight_layout()
    return fig


def plot_line_utilizations(subgrid: SubGridInfo, threshold: float = 0.5, width: int = 16, height: int = 6,
                           show_legend: bool = False):
    line_utilisation = subgrid.line_utilisation
    df = line_utilisation[[i for i, value in line_utilisation.max().to_dict().items() if value > threshold]]

    if df.empty:
        fig = plt.plot()
    else:
        fig = df.plot(figsize=(width, height), legend=show_legend)

    fig.tight_layout()
    return fig


def plot_with_highlights(grid: GridContainer):
    mv_20 = get_nodes(grid, 20.0)
    mv_10 = get_nodes(grid, 10.0)
    mv_30 = get_nodes(grid, 30.0)
    hv = get_nodes(grid, 110.0)

    mv_lines = get_lines(grid, 10.0) + get_lines(grid, 20.0) + get_lines(grid, 30.0)

    node_highlights = {
        RED: mv_10,
        ORANGE: mv_20,
        BROWN: mv_30,
        PURPLE: hv
    }

    line_highlights = {
        YELLOW: mv_lines
    }

    return grid_plot(grid, background="white-bg", node_highlights=node_highlights, line_highlights=line_highlights)
