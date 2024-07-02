from os import listdir
from os.path import join
from typing import Union

from matplotlib import pyplot as plt

from pypsdm import GridWithResults, Transformers2W, GridResultContainer, NodesResult, GridContainer
from pypsdm.ma_thesis.analyse import analyse_nodes, get_max_voltages, get_min_voltages
from pypsdm.ma_thesis import get_nodes, get_lines
from pypsdm.ma_thesis.subgrid import SubGridInfo, SubGrid
from pypsdm.ma_thesis.utils import get_trafo_2w_info
from pypsdm.models.result.container.raw_grid import Transformers2WResult
from pypsdm.plots.common.utils import *
from pypsdm.plots.grid import grid_plot


def plot_voltages_with_scenario(
        subgrid: SubGrid,
        results: dict[str, GridResultContainer],
        upper_limit: float = None,
        lower_limit: float = None,
        width: int = 12,
        height: int = 6
):
    fig, axes = plt.subplots(2, 1, figsize=(width, height), sharex=True)

    node_res = {name: res.nodes for name, res in results.items()}
    get_max_voltages(subgrid.grid, node_res).plot(ax=axes[0])
    get_min_voltages(subgrid.grid, node_res).plot(ax=axes[1])

    ax_added_dotted(axes[0], upper_limit)
    ax_added_dotted(axes[1], lower_limit)

    return fig

def plot_voltage_with_tapping(
        subgrid: SubGrid,
        transformer_uuids: list[str],
        results: GridResultContainer,
        dotted: Union[float | list[float]] = None,
        width: int = 12,
        height: int = 6
):
    fig, axes = plt.subplots(2, 1, figsize=(width, height), sharex=True)

    ax_plot_both_voltages(axes[0], subgrid, results.nodes, dotted)
    ax_plot_tapping(axes[1], transformer_uuids, subgrid.grid.transformers_2_w, results.transformers_2w)

    return fig


def ax_plot_both_voltages(
        axes: Axes,
        subgrid: SubGrid,
        results: NodesResult,
        dotted: Union[float | list[float]] = None
):
    _, node_min_max_res = analyse_nodes(subgrid.name, subgrid.grid, results)

    node_min_max_res.plot(ax=axes)
    ax_added_dotted(axes, dotted)


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
    tap_pos.plot(ax=axes, drawstyle="steps-post")


def plot_voltages_with_tapping(subgrid1: SubGridInfo, subgrid2: SubGridInfo, transformers: Transformers2W,
                               transformer_res: Transformers2WResult, dotted: Union[float | list[float]] = None,
                               width: int = 12, height: int = 6):
    connectors = list(set(subgrid1.get_transformers()).intersection(subgrid2.get_transformers()))

    tap_pos = pd.concat({transformers[uuid].id: transformer_res[uuid].data["tap_pos"] for uuid in connectors}, axis=1)

    fig, axes = plt.subplots(3, 1, figsize=(width, height), sharex=True)

    subgrid1.node_min_max.plot(ax=axes[0])
    subgrid2.node_min_max.plot(ax=axes[1])
    tap_pos.plot(ax=axes[2])

    if dotted:
        if isinstance(dotted, float):
            [axes[i].axhline(dotted, color="red", linestyle="--") for i in range(0, 2)]
        else:
            [axes[i].axhline(dot, color="red", linestyle="--") for dot in dotted for i in range(0, 2)]

    return fig


def plot_voltage_subgrid(subgrid: SubGridInfo, width: int = 12, height: int = 6):
    return subgrid.node_res.plot(figsize=(width, height), legend=False)


def plot_subgrid_with_versions(subgrids: dict[str, SubGridInfo], dotted: Union[float | list[float]] = None,
                               width: int = 12, height: int = 6):
    fig, axes = plt.subplots(len(subgrids), ncols=1, sharex=True, figsize=(width, height))

    for i, key in enumerate(subgrids):
        subgrids[key].node_min_max.plot(ax=axes[i])

        if dotted:
            if isinstance(dotted, float):
                axes[i].axhline(dotted, color="red", linestyle="--")
            else:
                [axes[i].axhline(dot, color="red", linestyle="--") for dot in dotted]

        axes[i].set_title(key)

    return fig


def plot_voltage_subgrids(subgrids: dict[int, SubGridInfo], dotted: Union[float | list[float]] = None, width: int = 12,
                          height: int = 6, subplots: bool = True):
    if subplots:
        fig, axes = plt.subplots(nrows=len(subgrids), ncols=1, sharex=True)
        fig.set_figheight(height)
        fig.set_figwidth(width)

        for i, subgrid in enumerate(subgrids.values()):
            subgrid.node_min_max.plot(ax=axes[i])

            if dotted:
                if isinstance(dotted, float):
                    axes[i].axhline(dotted, color="red", linestyle="--")
                else:
                    [axes[i].axhline(dot, color="red", linestyle="--") for dot in dotted]

    else:
        values = [subgrid.node_min_max for subgrid in subgrids.values()]
        fig, axes = pd.concat(values, axis=1).plot()

        if dotted:
            if isinstance(dotted, float):
                axes.axhline(dotted, color="red", linestyle="--")
            else:
                [axes.axhline(dot, color="red", linestyle="--") for dot in dotted]

    return fig


def plot_transformer_tappings(gwr: GridWithResults, width: int = 12, height: int = 6, subplots: bool = True):
    transformers = get_trafo_2w_info(gwr)
    transformer_results = gwr.transformers_2_w_res

    res = {tr_info.id: transformer_results[uuid].data["tap_pos"] for uuid, tr_info in transformers.items()}
    res_sorted = dict(sorted(res.items()))

    tap_pos = pd.concat(res_sorted, axis=1)
    fig = tap_pos.plot(subplots=subplots, figsize=(width, height))

    return fig


def plot_line_utilizations(subgrid: SubGridInfo, threshold: float = 0.5, width: int = 12, height: int = 6,
                           show_legend: bool = False):
    line_utilisation = subgrid.line_utilisation
    df = line_utilisation[[i for i, value in line_utilisation.max().to_dict().items() if value > threshold]]

    if df.empty:
        fig = plt.plot()
    else:
        fig = df.plot(figsize=(width, height), legend=show_legend)

    return fig


def plot_voltage_with_congestion(
        subgrid: SubGridInfo,
        result: GridResultContainer,
        dotted: Union[float | list[float]] = None,
        width: int = 12,
        height: int = 6
):
    fig, axes = plt.subplots(2, 1, figsize=(width, height), sharex=True)

    subgrid.node_min_max.plot(ax=axes[0])

    congestions = result.congestions[subgrid.sub_grid.nr].voltage * 1

    axes[0].set_ylabel("Spannung in pu")

    axes[1].set_yticks([0, 1])
    axes[1].set_yticklabels(["nein", "ja"])
    axes[1].set_ylabel("Engpass?")

    if dotted:
        if isinstance(dotted, float):
            axes[0].axhline(dotted, color="red", linestyle="--")
        else:
            [axes[0].axhline(dot, color="red", linestyle="--") for dot in dotted]

    congestions.plot(ax=axes[1], drawstyle="steps-post")

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


def get_plot(path: str,
             delimiter=",",
             primary_data_delimiter=","):
    gwr = GridContainer.from_csv(path, delimiter, primary_data_delimiter)

    return plot_with_highlights(gwr)


def get_plots(path: str, delimiter=";", primary_data_delimiter=";"):
    files = [join(path, file) for file in listdir(path)]

    grids = list()

    for file in files:
        grids.append(get_plot(file, delimiter, primary_data_delimiter))

    return grids
