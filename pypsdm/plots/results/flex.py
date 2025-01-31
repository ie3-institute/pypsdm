from functools import partial

from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.result.container.participants import (
    SystemParticipantsResultContainer,
)
from pypsdm.models.result.participant.flex_options import FlexOption
from pypsdm.models.ts.types import ComplexPower
from pypsdm.plots.common.line_plot import ax_plot_time_series
from pypsdm.plots.common.utils import (
    FIGSIZE,
    FLEX_MAX,
    FLEX_MIN,
    FLEX_REF,
    ORANGE,
    Resolution,
    set_title,
)
from pypsdm.plots.results.power import ax_plot_active_power


def plot_all_participants_flex_range(
    participants_res_container: SystemParticipantsResultContainer,
    title: str = "Participants Flex Range",
    hourly_mean: bool = False,
    include_actual_res=False,
    resolution: Resolution | None = None,
):

    em_res_dict = {}
    for entity_type, participant_res in participants_res_container.to_dict().items():
        if not participant_res:
            continue
        if entity_type not in {
            SystemParticipantsEnum.LOAD,
            SystemParticipantsEnum.ENERGY_MANAGEMENT,
            SystemParticipantsEnum.FLEX_OPTIONS,
        }:
            em_res_dict[entity_type] = participant_res
    plot_count = len(em_res_dict)

    fig, axs = plt.subplots(plot_count, 1, figsize=(10, 11), sharex=True, sharey=False)
    fig.suptitle(title)
    plt.subplots_adjust(hspace=0.5)

    for idx, (entity_type, participant_res) in enumerate(em_res_dict.items()):
        participant_flex = participants_res_container.flex.subset(
            participant_res.keys()
        )
        if participant_flex:
            flex_sum = participant_flex.sum()
            axs[idx].set_title(f"{participant_res.entity_type.get_plot_name()}")
            ax_plot_flex_range(
                axs[idx], flex_sum, hourly_mean=hourly_mean, resolution=resolution
            )
        if include_actual_res:
            ax_plot_active_power(
                axs[idx],
                participant_res.sum() * 1e3,
                hourly_mean=hourly_mean,
                color=ORANGE,
                label="p_actual",
                resolution=resolution,
            )
        axs[idx].legend()
        axs[idx].set_ylabel("Power in kW")

    return fig, axs


def plot_flex_range(
    flex_option: FlexOption,
    title: str,
    hourly_mean: bool = False,
    actual_res: ComplexPower | None = None,
    resolution: Resolution | None = None,
):
    figure, ax = plt.subplots(figsize=FIGSIZE)
    # plt.tight_layout()
    ax_plot_flex_range(ax, flex_option, hourly_mean, actual_res, resolution=resolution)
    title = title if title else "Flex Options"

    set_title(ax, title)
    return figure, ax


def ax_plot_flex_range(
    ax: Axes,
    flex_option: FlexOption,
    hourly_mean: bool,
    actual_res: ComplexPower | None = None,
    resolution: Resolution | None = None,
):
    p_ref = flex_option.p_ref() * 1e3
    plot_func = partial(
        ax_plot_time_series,
        ax=ax,
        entity_type=SystemParticipantsEnum.FLEX_OPTIONS,
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
            hourly_mean=hourly_mean,
            color=ORANGE,
            label="p_actual",
            resolution=resolution,
        )

    ax.set_ylabel("Power in kW")

    ax.legend()
