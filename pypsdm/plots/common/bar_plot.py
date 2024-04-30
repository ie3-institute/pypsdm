import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

from pypsdm.models.enums import EntitiesEnum
from pypsdm.models.result.container.participants import (
    SystemParticipantsResultContainer,
)
from pypsdm.models.ts.types import ComplexPower
from pypsdm.plots.common.utils import (
    FIGSIZE,
    FIGSIZE_WIDE,
    LOAD_COLOR,
    PV_COLOR,
    TITLE_FONT_SIZE,
    get_label_and_color,
)

sns.set_style("whitegrid")


def plot_full_load_hours(
    res: ComplexPower,
    device_power_kw,
    entity_type: None | EntitiesEnum = None,
    period="M",
    title=None,
):
    """
    Plots full load hours of the system in each period (e.g. Y, M, D for year, month, day).
    """
    if not title:
        title = "Full load hours"

    full_load_hours = res.full_load_hours(device_power_kw, period=period)
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    _, color = get_label_and_color(entity_type)
    ax.bar([x for x in range(len(full_load_hours))], full_load_hours, color=color)

    # Set x-tick labels
    ax.set_xticks(range(len(full_load_hours)))
    ax.set_xticklabels(
        full_load_hours.index.astype(str), rotation=45, ha="right"
    )  # Rotate labels for better visibility

    ax.set_ylabel("Usage in hours")
    ax.set_xlabel("Period")

    ax.set_title(title, fontsize=TITLE_FONT_SIZE, pad=15)
    plt.show()
    return fig, ax


def plot_load_and_generation(participant_res: SystemParticipantsResultContainer):
    """
    Plots the energy consumption and generation of each participant type.
    """
    lg_dict = participant_res.load_and_generation_energies()
    keys = []
    load = []
    generation = []
    for key, load_generation in lg_dict.items():
        keys.append(key)
        load.append(load_generation[0])
        generation.append(load_generation[1])
    keys = [key.value for key in lg_dict.keys()]
    fig, axs = plt.subplots(figsize=FIGSIZE, ncols=2, sharey=True)
    plt.subplots_adjust(wspace=0)

    x_lim = max(max(load), abs(min(generation))) * 1.2

    bars_generation = axs[0].barh(
        keys,
        generation,
        align="center",
        color=PV_COLOR,
        edgecolor=PV_COLOR,
        zorder=10,
    )
    axs[0].set_title("Generation", fontsize=TITLE_FONT_SIZE, pad=15)
    axs[0].set_xlim(left=-x_lim)
    axs[0].bar_label(
        bars_generation,
        padding=4,
        labels=[f"{x:,.0f}" for x in bars_generation.datavalues],
    )
    axs[0].get_xaxis().set_major_formatter(
        FuncFormatter(lambda x, p: format(int(x), ","))
    )

    bars_load = axs[1].barh(keys, load, align="center", color=LOAD_COLOR, zorder=10)
    axs[1].bar_label(
        bars_load, padding=4, labels=[f"{x:,.0f}" for x in bars_load.datavalues]
    )
    axs[1].set_title("Load", fontsize=TITLE_FONT_SIZE, pad=15)
    axs[1].set_xlim(right=x_lim)
    axs[1].get_xaxis().set_major_formatter(
        FuncFormatter(lambda x, p: format(int(x), ","))
    )
    # this should work since mpl 3.4 but does not for some reason

    # axs[1].bar_label(bars_load)
    fig.tight_layout()
    plt.show()
