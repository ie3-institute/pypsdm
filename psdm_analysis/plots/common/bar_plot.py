import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

from psdm_analysis.models.result.participant.participants_res_container import (
    ParticipantsResultContainer,
)
from psdm_analysis.models.result.power import PQResult
from psdm_analysis.plots.utils import (
    FIGSIZE,
    FIGSIZE_WIDE,
    LOAD_COLOR,
    PV_COLOR,
    TITLE_FONT_SIZE,
    get_label_and_color,
)

sns.set_style("whitegrid")


def daily_usage(res: PQResult, device_power_mw):
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    usage_hours = res.daily_usage(device_power_mw)
    label, color = get_label_and_color(res.type)
    ax.bar(usage_hours.index, usage_hours, color=color)
    ax.set_ylabel("Daily usage in hours")
    ax.set_xlabel("Day of year")


def plot_load_and_generation(participant_res: ParticipantsResultContainer):
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
        alpha=0.7,
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
        mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ","))
    )

    bars_load = axs[1].barh(
        keys, load, align="center", color=LOAD_COLOR, alpha=0.7, zorder=10
    )
    axs[1].bar_label(
        bars_load, padding=4, labels=[f"{x:,.0f}" for x in bars_load.datavalues]
    )
    axs[1].set_title("Load", fontsize=TITLE_FONT_SIZE, pad=15)
    axs[1].set_xlim(right=x_lim)
    axs[1].get_xaxis().set_major_formatter(
        mpl.ticker.FuncFormatter(lambda x, p: format(int(x), ","))
    )
    # this should work since mpl 3.4 but does not for some reason

    # axs[1].bar_label(bars_load)
    fig.tight_layout()
    plt.show()
