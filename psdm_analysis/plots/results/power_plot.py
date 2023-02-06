from functools import partial
from typing import Union

import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from psdm_analysis.models.input.participant.participant import (
    SystemParticipantsWithCapacity,
)
from psdm_analysis.models.result.participant.participant import (
    ParticipantsResult,
    ParticipantsWithSocResult,
)
from psdm_analysis.models.result.participant.participants_res_container import (
    ParticipantsResultContainer,
)
from psdm_analysis.models.result.power import PQResult, PQWithSocResult
from psdm_analysis.plots.results.line_plot import ax_plot_time_series
from psdm_analysis.plots.utils import (
    FIGSIZE,
    FILL_ALPHA,
    LOAD_COLOR,
    PV_COLOR,
    add_to_kwargs_if_not_exist,
    get_label_and_color,
    get_label_and_color_dict,
    legend_with_distinct_labels,
    plot_resample,
    set_date_format_and_label,
    set_title,
)

sns.set_style("whitegrid")


def plot_comparison(
    res_a: PQResult,
    res_b: PQResult,
    label_a: str,
    label_b: str,
    title: str,
    resolution: str,
    hourly_mean=False,
    flex_signal: PQResult = None,
):
    subplot_count = 2 if flex_signal is None else 3
    fig, axs = plt.subplots(
        subplot_count, 1, figsize=FIGSIZE, sharex=True, sharey=False
    )
    ax_plot_active_power_result(
        axs[0], res_a, resolution, hourly_mean, label=label_a, color=LOAD_COLOR
    )
    ax_plot_active_power_result(
        axs[0], res_b, resolution, hourly_mean, label=label_b, color=PV_COLOR
    )
    residual = res_a - res_b
    ax_plot_active_power_result(
        axs[1], residual, resolution, hourly_mean, label="Residual Load"
    )
    if flex_signal:
        ax_plot_active_power_result(
            axs[2], flex_signal, resolution, hourly_mean, label="Flex Signal"
        )
    fig.suptitle(title)
    [ax.legend() for ax in axs]
    return axs, fig


def plot_em(
    em_participant_results: ParticipantsResultContainer,
    resolution: str,
    hourly_mean: bool = False,
):
    em_uuid = list(em_participant_results.ems.participants.keys())[0]

    title = f"Household: {em_uuid}"

    fig, axs = plt.subplots(2, 1, figsize=(10, 5), sharex=True, sharey=True)
    axs[0].set_title(title)

    ax_plot_participants(
        axs[0], em_participant_results, resolution, hourly_mean=hourly_mean, stack=True
    )
    ax_plot_active_power_result(
        axs[1],
        em_participant_results.ems.sum(),
        resolution,
        hourly_mean=hourly_mean,
        fill_from_index=True,
    )
    return fig


def plot_aggregated_load_and_generation(
    participants: Union[ParticipantsResultContainer, list[PQResult]],
    title: str,
    resolution: str,
    hourly_mean: bool,
    with_residual=True,
):
    if with_residual:
        fig, axs = plt.subplots(2, 1, figsize=(10, 5), sharex=True, sharey=True)
        pq_results = _get_pq_results_from_union(participants)
        all_load, all_generation = zip(
            *[pq_result.divide_load_generation() for pq_result in pq_results]
        )
        agg_load = PQResult.sum(all_load)
        agg_generation = PQResult.sum(all_generation)
        ax_plot_active_power_result(
            axs[0],
            agg_load,
            resolution,
            hourly_mean,
            fill_from_index=True,
            color=LOAD_COLOR,
            label="Aggregated Load",
        )
        ax_plot_active_power_result(
            axs[0],
            agg_generation,
            resolution,
            hourly_mean,
            fill_from_index=True,
            color=PV_COLOR,
            label="Aggregated Generation",
        )
        ax_plot_active_power_result(
            axs[1],
            PQResult.sum([agg_load, agg_generation]),
            resolution,
            hourly_mean,
            fill_from_index=True,
            color=LOAD_COLOR,
            label="Residual Load",
        )
        set_title(axs[0], title)
        axs[0].legend(loc=7)
        axs[1].legend()
        return fig, axs


def plot_all_participants(
    participants: Union[ParticipantsResultContainer, list[PQResult]],
    title: str,
    resolution: str,
    hourly_mean: bool,
    stack=False,
    with_residual=False,
    **kwargs,
):
    if with_residual:
        fig, axs = plt.subplots(2, 1, figsize=(10, 5), sharex=True, sharey=True)
        ax_plot_participants(
            axs[0], participants, resolution, hourly_mean, stack, **kwargs
        )
        participants_sum = (
            participants.sum()
            # here I would usually check if participants is a ParticipantsResultContainer
            # but for some weird reason this returns False every time
            if not isinstance(participants, list)
            else PQResult.sum(participants)
        )
        ax_plot_active_power_result(
            axs[1],
            participants_sum,
            resolution,
            hourly_mean,
            fill_from_index=True,
            **kwargs,
        )
        set_title(axs[0], title)
    else:
        fig, axs = plt.subplots(figsize=FIGSIZE)
        ax_plot_participants(
            axs, participants, resolution, hourly_mean, stack, **kwargs
        )
        set_title(axs, title)
    return fig, axs


def _get_pq_results_from_union(
    participants: Union[ParticipantsResultContainer, list[PQResult]]
) -> list[PQResult]:
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
    participants: Union[ParticipantsResultContainer, list[PQResult]],
    resolution: str,
    hourly_mean: bool = False,
    stack=False,
    **kwargs,
):
    pq_results = _get_pq_results_from_union(participants)
    if stack:
        plot_kwargs = [kwargs for _ in range(len(pq_results))]
        ax_plot_stacked_pq(ax, pq_results, resolution, hourly_mean, plot_kwargs)
    else:
        [
            ax_plot_active_power_result(
                ax, pq_result, resolution, hourly_mean, **kwargs
            )
            for pq_result in pq_results
        ]
    legend_with_distinct_labels(ax)


def ax_plot_stacked_pq(
    ax: Axes,
    results: [PQResult],
    resolution: str,
    hourly_mean: bool = False,
    plot_kwargs: [dict] = None,
):
    residual_load, residual_generation = results[0].divide_load_generation()

    plot_partial = partial(
        ax_plot_active_power_result,
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

        if load.p.sum() > 0:
            load_sum = PQResult(
                res.type, "", "", PQResult.sum([load, residual_load]).data
            )
            plot_partial(
                res=load_sum,
                fill_between=residual_load.p,
                **plot_kwargs[idx + 1] if plot_kwargs else {},
            )
            residual_load = load_sum

        if generation.p.sum() < 0:
            generation_sum = PQResult(
                res.type, "", "", PQResult.sum([generation, residual_generation]).data
            )
            plot_partial(
                res=generation_sum,
                fill_between=residual_generation.p,
                **plot_kwargs[idx + 1] if plot_kwargs else {},
            )
            residual_generation = generation_sum
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())


def plot_participants_sum(
    res: ParticipantsResult,
    title: str,
    resolution: str,
    hourly_mean: bool = False,
    fill_from_index: bool = True,
    **kwargs,
):
    if not isinstance(res, ParticipantsResult):
        raise TypeError(
            "Data must be of type ParticipantsResult but is {}".format(type(res))
        )
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax_plot_active_power_result(
        ax, res.sum(), resolution, hourly_mean, fill_from_index, **kwargs
    )
    set_title(ax, title)
    return fig


def plot_participants_with_soc_sum(
    res: ParticipantsWithSocResult,
    input: SystemParticipantsWithCapacity,
    title: str,
    resolution: str,
    hourly_mean: bool = False,
    fill_from_index: bool = True,
    **kwargs,
):
    fig, axs = plt.subplots(2, 1, figsize=FIGSIZE, sharex=True, sharey=False)
    axs[0].set_title(title)
    sum = ParticipantsWithSocResult.sum_with_soc(res, input)
    ax_plot_active_power_result(
        axs[0],
        sum,
        resolution,
        hourly_mean=hourly_mean,
        fill_from_index=fill_from_index,
        **kwargs,
    )
    ax_plot_soc(axs[1], sum, resolution, hourly_mean, fill_from_index, **kwargs)
    return fig


def plot_active_power(
    res: PQResult,
    title: str,
    resolution: str,
    hourly_mean: bool,
    fill_from_index=True,
    **kwargs,
):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.set_ylabel("Power in MW")
    ax_plot_active_power_result(
        ax, res, resolution, hourly_mean, fill_from_index=fill_from_index, **kwargs
    )
    set_title(ax, title)
    return fig, ax


def ax_plot_active_power_result(
    ax: Axes,
    res: PQResult,
    resolution: str,
    hourly_mean: bool = False,
    fill_from_index: bool = False,
    fill_between=None,
    **kwargs,
):
    if len(res.p) == 0:
        raise ValueError("Active power time series is empty. No data to plot")

    ax = ax_plot_time_series(
        ax,
        res.p,
        res.type,
        resolution,
        hourly_mean,
        fill_from_index,
        fill_between,
        **kwargs,
    )
    ax.set_ylabel("Power in MW")


def ax_plot_soc(
    ax: Axes,
    res: PQWithSocResult,
    resolution: str,
    hourly_mean: bool = False,
    fill_from_index=False,
    **kwargs,
):
    label, color = get_label_and_color(res.type)
    set_date_format_and_label(ax, resolution)
    ax.set_ylabel("SOC in percent")
    soc = plot_resample(res.soc(), hourly_mean)
    ax.plot(soc, color=color, label=label, **kwargs)
    ax.set_ylim(bottom=0, top=100)
    if fill_from_index:
        ax.fill_between(soc.index, soc, alpha=FILL_ALPHA, color=color)


def plot_sorted_annual_load_duration(
    res: PQResult, s_rated_mw: float = None, fill_from_index=False, **kwargs
):
    args = get_label_and_color_dict(res.type)
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
