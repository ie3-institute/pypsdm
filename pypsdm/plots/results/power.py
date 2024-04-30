from functools import partial
from typing import Optional, Union

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from pypsdm.models.enums import EntitiesEnum
from pypsdm.models.gwr import GridWithResults
from pypsdm.models.input.participant.participant import SystemParticipantsWithCapacity
from pypsdm.models.result.container.participants import (
    SystemParticipantsResultContainer,
)
from pypsdm.models.ts.base import EntityKey
from pypsdm.models.ts.mixins import ComplexPowerMixin, SocMixin
from pypsdm.models.ts.types import (
    ComplexPower,
    ComplexPowerDict,
    ComplexPowerWithSoc,
    ComplexPowerWithSocDict,
    ComplexVoltagePowerDict,
)
from pypsdm.plots.common.line_plot import ax_plot_time_series
from pypsdm.plots.common.utils import (
    BLUE,
    FIGSIZE,
    FILL_ALPHA,
    GREEN,
    LOAD_COLOR,
    ORANGE,
    PV_COLOR,
    RED,
    Resolution,
    add_to_kwargs_if_not_exist,
    get_label_and_color_dict,
    legend_with_distinct_labels,
    set_subplot_title,
    set_title,
    set_xlabels_rotated,
    set_ylabel,
)


def plot_apparent_power_components(
    power: ComplexPower,
    name: EntityKey | str | None = None,
    title: str | None = None,
    resolution: Resolution | None = None,
):
    """
    Plots apparent power components (magnitude, active, reactive, angle) for a given
    pq result.

    Args
        pq: ComplexPower
        resolution: Resolution of the plot
        title: Optional title of the plot
    """
    fig, axs = plt.subplots(4, 1, figsize=(15, 16))

    fig.subplots_adjust(hspace=0.4)

    ax_plot_power_mag(axs[0], power, resolution=resolution, color=RED)
    axs[0].set_title("Apparent Power")
    ax_plot_active_power(axs[1], power, resolution=resolution, color=GREEN)
    axs[1].set_title("Active Power")
    ax_plot_reactive_power(axs[2], power, resolution=resolution, color=BLUE)
    axs[2].set_title("Reactive Power")
    ax_plot_power_angle(axs[3], power, resolution=resolution, color=ORANGE)
    axs[3].set_title("Power Angle")

    if title is None:
        if name:
            if isinstance(name, EntityKey):
                name = name.id
            title = f"Apparent Power Components: {name}"
        else:
            title = "Apparent Power Composition"

    fig.suptitle(title, fontsize=16, y=0.93)

    return fig, axs


def plot_all_nodal_ps_branch_violin(
    gwr: GridWithResults,
    **kwargs,
):
    """
    Plots active power violin plots for all nodes across all branches.

    Args:
        gwr: GridWithResults object
        exclude: Optional list of node uuids that should be excluded from the plot.

    Returns:
        fig, axes
    """
    branches = gwr.grid.raw_grid.get_branches()
    nodes_res = gwr.build_extended_nodes_result()
    width, height = FIGSIZE
    height = height * len(branches)
    fig, axes = plt.subplots(nrows=len(branches), figsize=(width, height))
    for i, branch in enumerate(branches):
        ax = axes[i] if len(branches) > 1 else axes
        ax_plot_nodal_ps_violin(ax, nodes_res, branch, **kwargs)  # type: ignore
        set_subplot_title(ax, f"Nodal Actice Power Along Branch {i+1}")
    plt.tight_layout()

    return fig, axes


def plot_nodal_ps_violin(
    extended_nodes_res: ComplexVoltagePowerDict,
    nodes: Optional[list[str]] = None,
    **kwargs,
):
    """
    Plots violin plots for all given nodes.

    Args:
        extended_nodes_res: ExtendedNodesResult to plot.
        nodes: Optional list of node uuids that should be plotted. Order is preserved.
    Returns:
        fig, ax
    """
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_nodal_ps_violin(ax, extended_nodes_res, nodes, **kwargs)
    plt.grid(True)
    set_title(ax, "Nodal Active Power")
    return fig, ax


def ax_plot_nodal_ps_violin(
    ax: Axes,
    nodes_res: ComplexVoltagePowerDict,
    nodes: Optional[list[str]],  # branches can be found by GridContainer.get_branches()
    **kwargs,
):
    """
    Plots violin plots for given nodes. If no nodes are passed all nodes are plotted.

    Args:
        ax: Axes object
        nodes_res: NodesResult or ExtendedNodesResult object
        nodes: Optional list of node uuids that should be plotted. Order is preserved.
        exclude: Optional list of node uuids that should be excluded from the plot.
    """

    if nodes:
        p = nodes_res.subset(nodes).p(favor_ids=False).reindex(columns=nodes)
        uuid_id_map = {k.uuid: k.id for k in nodes_res.keys()}
        p.columns = [uuid_id_map[col] for col in p.columns]
    else:
        p = nodes_res.p()

    data = []
    for col in p.columns:
        data.append((p[col].dropna() * 1e3).values)

    ax.violinplot(data, **kwargs)

    # set labels
    x_labels = list(p.columns)
    set_xlabels_rotated(ax, x_labels, ha="right")
    set_ylabel(ax, "Nodal active power in kW")
    _ = ax.set_xticklabels(x_labels, rotation=45, ha="right")


def plot_comparison(
    res_a: ComplexPower,
    res_b: ComplexPower,
    label_a: str,
    label_b: str,
    title: str,
    hourly_mean=False,
    flex_signal: ComplexPower | None = None,
    resolution: Resolution | None = None,
):
    subplot_count = 2 if flex_signal is None else 3
    fig, axs = plt.subplots(
        subplot_count, 1, figsize=FIGSIZE, sharex=True, sharey=False
    )
    ax_plot_active_power(
        axs[0],
        res_a,
        hourly_mean=hourly_mean,
        label=label_a,
        color=LOAD_COLOR,
        resolution=resolution,
    )
    ax_plot_active_power(
        axs[0],
        res_b,
        hourly_mean=hourly_mean,
        label=label_b,
        color=PV_COLOR,
        resolution=resolution,
    )
    residual = res_a - res_b
    ax_plot_active_power(
        axs[1],
        residual,
        hourly_mean=hourly_mean,
        label="Residual Load",
        resolution=resolution,
    )
    if flex_signal:
        ax_plot_active_power(
            axs[2],
            flex_signal,
            hourly_mean=hourly_mean,
            label="Flex Signal",
            resolution=resolution,
        )
    fig.suptitle(title)
    [ax.legend() for ax in axs]
    return axs, fig


def plot_em(
    em_participant_results: SystemParticipantsResultContainer,
    hourly_mean: bool = False,
    resolution: Resolution | None = None,
):
    em_uuid = list(em_participant_results.ems.data.keys())[0]

    title = f"Household: {em_uuid}"

    fig, axs = plt.subplots(2, 1, figsize=(10, 5), sharex=True, sharey=True)
    axs[0].set_title(title)

    ax_plot_participants(
        axs[0],
        em_participant_results,
        hourly_mean=hourly_mean,
        stack=True,
        resolution=resolution,
    )
    ax_plot_active_power(
        axs[1],
        em_participant_results.ems.sum(),
        hourly_mean=hourly_mean,
        fill_from_index=True,
        resolution=resolution,
    )
    return fig, axs


def plot_aggregated_load_and_generation(
    participants: Union[SystemParticipantsResultContainer, list[ComplexPower]],
    title: str = "Aggregated Load and Generation",
    hourly_mean: bool = False,
    resolution: Resolution | None = None,
    with_residual=True,
):
    if with_residual:
        fig, axs = plt.subplots(2, 1, figsize=(10, 5), sharex=True, sharey=True)
        pq_results = _get_pq_results_from_union(participants)
        all_load, all_generation = zip(
            *[pq_result.divide_load_generation() for pq_result in pq_results]
        )
        agg_load = ComplexPower.sum(all_load)
        agg_generation = ComplexPower.sum(all_generation)
        ax_plot_active_power(
            axs[0],
            agg_load,
            hourly_mean=hourly_mean,
            fill_from_index=True,
            color=LOAD_COLOR,
            label="Aggregated Load",
            resolution=resolution,
        )
        ax_plot_active_power(
            axs[0],
            agg_generation,
            hourly_mean=hourly_mean,
            fill_from_index=True,
            color=PV_COLOR,
            label="Aggregated Generation",
            resolution=resolution,
        )
        ax_plot_active_power(
            axs[1],
            ComplexPower.sum([agg_load, agg_generation]),
            hourly_mean=hourly_mean,
            fill_from_index=True,
            color=LOAD_COLOR,
            label="Residual Load",
            resolution=resolution,
        )
        set_title(axs[0], title)
        axs[0].legend(loc=7)
        axs[1].legend()
        return fig, axs


def plot_all_participants(
    participants: Union[SystemParticipantsResultContainer, list[ComplexPower]],
    title: str,
    hourly_mean: bool,
    stack=False,
    with_residual=False,
    resolution: Resolution | None = None,
    **kwargs,
):
    if with_residual:
        fig, axs = plt.subplots(2, 1, figsize=(10, 5), sharex=True, sharey=True)
        ax_plot_participants(
            axs[0], participants, hourly_mean, stack, resolution, **kwargs
        )
        participants_sum = (
            participants.sum()
            # here I would usually check if participants is a ParticipantsResultContainer
            # but for some weird reason this returns False every time
            if not isinstance(participants, list)
            else ComplexPower.sum(participants)
        )
        ax_plot_active_power(
            axs[1],
            participants_sum,
            hourly_mean=hourly_mean,
            fill_from_index=True,
            resolution=resolution,
            **kwargs,
        )
        set_title(axs[0], title)
    else:
        fig, axs = plt.subplots(figsize=FIGSIZE)
        ax_plot_participants(
            axs,
            participants,
            hourly_mean=hourly_mean,
            stack=stack,
            resolution=resolution,
            **kwargs,
        )
        set_title(axs, title)
    return fig, axs


def _get_pq_results_from_union(
    participants: Union[SystemParticipantsResultContainer, list[ComplexPower]],
) -> list[ComplexPower]:
    return (
        participants
        if isinstance(participants, list)
        else [
            participant.sum()
            for participant in participants.to_list(
                include_em=False, include_flex=False
            )
            if participant
        ]
    )


def ax_plot_participants(
    ax: Axes,
    participants: Union[SystemParticipantsResultContainer, list[ComplexPower]],
    hourly_mean: bool = False,
    stack=False,
    resolution: Resolution | None = None,
    **kwargs,
):
    pq_results = _get_pq_results_from_union(participants)
    if stack:
        plot_kwargs = [kwargs for _ in range(len(pq_results))]
        ax_plot_stacked_pq(
            ax,
            pq_results,
            hourly_mean=hourly_mean,
            resolution=resolution,
            plot_kwargs=plot_kwargs,
        )
    else:
        [
            ax_plot_active_power(
                ax, pq_result, hourly_mean=hourly_mean, resolution=resolution, **kwargs
            )
            for pq_result in pq_results
        ]
    legend_with_distinct_labels(ax)


def ax_plot_stacked_pq(
    ax: Axes,
    results: list[ComplexPower],
    hourly_mean: bool = False,
    plot_kwargs: list[dict] | None = None,
    resolution: Resolution | None = None,
):
    residual_load, residual_generation = results[0].divide_load_generation()
    residual_load = ComplexPower(residual_load)
    residual_generation = ComplexPower(residual_generation)

    plot_partial = partial(
        ax_plot_active_power,
        ax=ax,
        resolution=resolution,
        hourly_mean=hourly_mean,
    )

    plot_partial(
        res=residual_load, fill_from_index=True, **plot_kwargs[0] if plot_kwargs else {}
    )
    plot_partial(
        res=residual_generation,
        fill_from_index=True,
        **plot_kwargs[0] if plot_kwargs else {},
    )

    for idx, res in enumerate(results[1:]):
        load, generation = res.divide_load_generation()
        load = ComplexPower(load)
        generation = ComplexPower(generation)

        if load.p.sum() > 0:
            load_sum = residual_load + load
            plot_partial(
                res=load_sum,
                fill_between=residual_load.p,
                **plot_kwargs[idx + 1] if plot_kwargs else {},
            )
            residual_load = load_sum

        if generation.p.sum() < 0:
            generation_sum = residual_generation + generation
            plot_partial(
                res=generation_sum,
                fill_between=residual_generation.p,
                **plot_kwargs[idx + 1] if plot_kwargs else {},
            )
            residual_generation = generation_sum
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(list(by_label.values()), list(by_label.keys()))


def plot_participants_sum(
    res: ComplexPowerDict,
    title: str,
    hourly_mean: bool = False,
    fill_from_index: bool = True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if not isinstance(res, ComplexPowerDict):
        raise TypeError(
            "Data must be of type ParticipantsResult but is {}".format(type(res))
        )
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_active_power(
        ax,
        res.sum(),
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        resolution=resolution,
        **kwargs,
    )
    set_title(ax, title)
    return fig, ax


def plot_participants_with_soc_sum(
    res: ComplexPowerWithSocDict,
    input: SystemParticipantsWithCapacity,
    title: str,
    hourly_mean: bool = False,
    fill_from_index: bool = True,
    resolution: Resolution | None = None,
    **kwargs,
):
    fig, axs = plt.subplots(2, 1, figsize=FIGSIZE, sharex=True, sharey=False)
    axs[0].set_title(title)
    # TODO FIX!!
    capacities = input.capacity.to_dict()
    sum = ComplexPowerWithSocDict.sum_with_soc(res, capacities)
    ax_plot_active_power(
        axs[0],
        sum,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        resolution=resolution,
        **kwargs,
    )
    ax_plot_soc(
        axs[1],
        sum,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        resolution=resolution,
        **kwargs,
    )
    return fig, axs


def plot_active_power_with_soc(
    res: ComplexPowerWithSoc,
    title: str,
    hourly_mean=False,
    fill_from_index=False,
    resolution: Resolution | None = None,
    **kwargs,
):
    fig, axs = plt.subplots(2, 1, figsize=FIGSIZE, sharex=True, sharey=False)
    axs[0].set_title(title)
    ax_plot_active_power(
        axs[0],
        res,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        set_x_label=False,
        resolution=resolution,
        **kwargs,
    )
    ax_plot_soc(
        axs[1],
        res,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        resolution=resolution,
        **kwargs,
    )
    return fig, axs


def plot_active_power(
    res: ComplexPower,
    name: EntityKey | str | None = None,
    entity_type: EntitiesEnum | None = None,
    title: Optional[str] = None,
    hourly_mean: bool = False,
    fill_from_index=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if not title:
        if name:
            if isinstance(name, EntityKey):
                name = name.id
            title = f"Active power: {name}"
        else:
            title = "Active power"
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.set_ylabel("Power in MW")
    ax_plot_active_power(
        ax,
        res,
        entity_type=entity_type,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        resolution=resolution,
        **kwargs,
    )
    set_title(ax, title)
    return fig, ax


def ax_plot_active_power(
    ax: Axes,
    res: ComplexPower,
    entity_type: EntitiesEnum | None = None,
    hourly_mean: bool = False,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if len(res.p) == 0:
        raise ValueError("Active power time series is empty. No data to plot")

    ax = ax_plot_time_series(
        ax,
        res.p * 1e3,
        entity_type=entity_type,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Power in kW")


def ax_plot_reactive_power(
    ax: Axes,
    res: ComplexPower,
    entity_type: EntitiesEnum | None = None,
    hourly_mean: bool = False,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    if len(res.q) == 0:
        raise ValueError("Reactive power time series is empty. No data to plot")

    ax = ax_plot_time_series(
        ax,
        res.q * 1e3,
        entity_type=entity_type,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Reactive Power in kVar")


def ax_plot_power_angle(
    ax: Axes,
    res: ComplexPower,
    entity_type: EntitiesEnum | None = None,
    hourly_mean: bool = False,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    angle = res.angle()
    if len(angle) == 0:
        raise ValueError("Angle time series is empty. No data to plot")

    ax = ax_plot_time_series(
        ax,
        angle,
        entity_type=entity_type,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Angle in degree")


def ax_plot_power_mag(
    ax: Axes,
    res: ComplexPowerMixin,
    entity_type: EntitiesEnum | None = None,
    hourly_mean: bool = False,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    complex_mag = res.complex_power().apply(lambda x: np.abs(x))
    if len(complex_mag) == 0:
        raise ValueError("Angle time series is empty. No data to plot")

    ax = ax_plot_time_series(
        ax,
        complex_mag,
        entity_type=entity_type,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("Apparent Power Magnitude in MVA")


def ax_plot_soc(
    ax: Axes,
    res: SocMixin,
    entity_type: EntitiesEnum | None = None,
    hourly_mean: bool = False,
    fill_from_index: bool = False,
    fill_between=None,
    set_x_label=True,
    resolution: Resolution | None = None,
    **kwargs,
):
    ax = ax_plot_time_series(
        ax,
        res.soc,
        entity_type=entity_type,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        fill_between=fill_between,
        set_x_label=set_x_label,
        resolution=resolution,
        **kwargs,
    )
    ax.set_ylabel("SOC in percent")
    ax.set_ylim(bottom=0, top=100)


def plot_sorted_annual_load_duration(
    res: ComplexPowerMixin,
    entity_type: EntitiesEnum | None = None,
    s_rated_mw: float | None = None,
    fill_from_index=False,
    **kwargs,
):
    args = get_label_and_color_dict(entity_type)
    kwargs = add_to_kwargs_if_not_exist(kwargs, args)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    annual_duartion_series = res.annual_duration_series()
    plt.plot(annual_duartion_series, **kwargs)
    set_title(ax, f"{kwargs['label']} Annual Load Duration Curve")
    ax.set_xlabel("Duration in hours")
    ax.set_ylabel("Rated power")
    if fill_from_index:
        ax.fill_between(
            annual_duartion_series.index,
            annual_duartion_series,
            alpha=FILL_ALPHA,
            color=kwargs["color"],
        )
    if s_rated_mw:
        # todo: implement right hand y-axis for displaying s_rated percentage
        pass
    return fig, ax
