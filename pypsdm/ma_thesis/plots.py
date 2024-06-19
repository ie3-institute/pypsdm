from typing import Union

import pandas as pd

from pypsdm import GridWithResults, Transformers2W
from matplotlib import pyplot as plt

from pypsdm.ma_thesis.utils import get_trafo_2w_info
from pypsdm.models.result.container.raw_grid import Transformers2WResult

from pypsdm.ma_thesis.SubnetInfo import SubnetInfo


def plot_voltage_with_tapping(subnet1: SubnetInfo, subnet2: SubnetInfo, transformers: Transformers2W,
                              transformer_res: Transformers2WResult, dotted: Union[float | list[float]] = None,
                              width: int = 12, height: int = 6):
    connectors = list(set(subnet1.transformers).intersection(subnet2.transformers))

    tap_pos = pd.concat({transformers[uuid].id: transformer_res[uuid].data["tap_pos"] for uuid in connectors}, axis=1)

    fig, axes = plt.subplots(3, 1, figsize=(width, height), sharex=True)

    subnet1.node_min_max.plot(ax=axes[0])
    subnet2.node_min_max.plot(ax=axes[1])
    tap_pos.plot(ax=axes[2])

    if dotted:
        if isinstance(dotted, float):
            [axes[i].axhline(dotted, color="red", linestyle="--") for i in range(0, 2)]
        else:
            [axes[i].axhline(dot, color="red", linestyle="--") for dot in dotted for i in range(0, 2)]

    return fig


def plot_voltage_subnet(subnet: SubnetInfo, width: int = 12, height: int = 6):
    return subnet.node_res.plot(figsize=(width, height), legend=False)


def plot_subnet_with_versions(subnets: dict[str, SubnetInfo], dotted: Union[float | list[float]] = None, width: int = 12, height: int = 6):
    fig, axes = plt.subplots(len(subnets), ncols=1, sharex=True, figsize=(width, height))

    for i, key in enumerate(subnets):
        subnets[key].node_min_max.plot(ax=axes[i])

        if dotted:
            if isinstance(dotted, float):
                axes[i].axhline(dotted, color="red", linestyle="--")
            else:
                [axes[i].axhline(dot, color="red", linestyle="--") for dot in dotted]

        axes[i].set_title(key)

    return fig


def plot_voltage_subnets(subnets: dict[int, SubnetInfo], dotted: Union[float | list[float]] = None, width: int = 12, height: int = 6, subplots: bool = True):
    if subplots:
        fig, axes = plt.subplots(nrows=len(subnets), ncols=1, sharex=True)
        fig.set_figheight(height)
        fig.set_figwidth(width)

        for i, subnet in enumerate(subnets.values()):
            subnet.node_min_max.plot(ax=axes[i])
            
            if dotted:
                if isinstance(dotted, float):
                    axes[i].axhline(dotted, color="red", linestyle="--")
                else:
                    [axes[i].axhline(dot, color="red", linestyle="--") for dot in dotted]

    else:
        values = [subnet.node_min_max for subnet in subnets.values()]
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


def plot_line_utilizations(subnet: SubnetInfo, threshold: float = 0.5, width: int = 12, height: int = 6,
                           show_legend: bool = False):
    line_utilisation = subnet.line_utilisation
    df = line_utilisation[[i for i, value in line_utilisation.max().to_dict().items() if value > threshold]]

    if df.empty:
        fig = plt.plot()
    else:
        fig = df.plot(figsize=(width, height), legend=show_legend)

    return fig
