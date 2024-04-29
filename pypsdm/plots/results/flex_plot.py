from functools import partial

from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.result.container.participants import (
    SystemParticipantsResultContainer,
)
from pypsdm.models.result.participant.flex_options import FlexOption
from pypsdm.models.result.power import PQResult
from pypsdm.plots.common.line_plot import ax_plot_time_series
from pypsdm.plots.common.utils import (
    FIGSIZE,
    FLEX_MAX,
    FLEX_MIN,
    FLEX_REF,
    ORANGE,
    set_title,
)
from pypsdm.plots.results.power_plot import ax_plot_active_power


def plot_all_participants_flex_range(
    participants_res_container: SystemParticipantsResultContainer,
    resolution: str,
    title: str = "Participants Flex Range",
    hourly_mean: bool = False,
    include_actual_res=False,
):
    em_res_list = [
        res
        for res in participants_res_container.to_list(
            include_em=False, include_flex=False, include_empty=False
        )
        if res.entity_type != SystemParticipantsEnum.LOAD
    ]
    plot_count = len(em_res_list)

    fig, axs = plt.subplots(plot_count, 1, figsize=(10, 11), sharex=True, sharey=False)
    fig.suptitle(title)
    plt.subplots_adjust(hspace=0.5)

    for idx, participant_res in enumerate(em_res_list):
        participant_flex = participants_res_container.flex.subset(
            participant_res.entities.keys()
        )
        if participant_flex:
            flex_sum = participant_flex.sum()
            axs[idx].set_title(f"{participant_res.entity_type.get_plot_name()}")
            ax_plot_flex_range(axs[idx], flex_sum, "d", hourly_mean=hourly_mean)
        if include_actual_res:
            ax_plot_active_power(
                axs[idx],
                participant_res.sum() * 1e3,
                resolution,
                hourly_mean=hourly_mean,
                color=ORANGE,
                label="p_actual",
            )
        axs[idx].legend()
        axs[idx].set_ylabel("Power in kW")

    return fig, axs


def plot_flex_range(
    flex_option: FlexOption,
    title: str,
    resolution: str,
    hourly_mean: bool,
    actual_res: PQResult | None = None,
):
    figure, ax = plt.subplots(figsize=FIGSIZE)
    # plt.tight_layout()
    ax_plot_flex_range(ax, flex_option, resolution, hourly_mean, actual_res)
    title = title if title else "Flex Options"

    set_title(ax, title)
    return figure, ax


def ax_plot_flex_range(
    ax: Axes,
    flex_option: FlexOption,
    resolution: str,
    hourly_mean: bool,
    actual_res: PQResult | None = None,
):
    p_ref = flex_option.p_ref() * 1e3
    plot_func = partial(
        ax_plot_time_series,
        ax=ax,
        type=EntitiesEnum.FLEX_OPTIONS,
        resolution=resolution,
        hourly_mean=hourly_mean,
    )

    plot_func(
        res=flex_option.p_max() * 1e3,
        label="p_max",
        color=FLEX_MAX,
        fill_between=p_ref,
    )
    plot_func(
        res=flex_option.p_min() * 1e3,
        label="p_min",
        color=FLEX_MIN,
        fill_between=p_ref,
    )
    plot_func(res=p_ref, label="p_ref", color=FLEX_REF)

    if actual_res:
        ax_plot_active_power(
            ax,
            actual_res,
            resolution,
            hourly_mean=hourly_mean,
            color=ORANGE,
            label="p_actual",
        )

    ax.set_ylabel("Power in kW")

    ax.legend()
