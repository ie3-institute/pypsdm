import os.path
from typing import Dict

import seaborn as sns
from matplotlib import dates as mdates
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from pandas import Series

from psdm_analysis.models.input.enums import EntitiesEnum, SystemParticipantsEnum
from psdm_analysis.processing.series import hourly_mean_resample

# === COLORS ===

COLOR_PALETTE = sns.color_palette()
BLUE = COLOR_PALETTE[0]
ORANGE = COLOR_PALETTE[1]
GREEN = COLOR_PALETTE[2]
RED = COLOR_PALETTE[3]
PURPLE = COLOR_PALETTE[4]
BROWN = COLOR_PALETTE[5]
PINK = COLOR_PALETTE[6]
GREY = COLOR_PALETTE[7]
YELLOW = COLOR_PALETTE[8]
LIGHT_BLUE = COLOR_PALETTE[9]

COLOR_PALETTE = sns.color_palette()
LOAD_COLOR = BLUE
PV_COLOR = GREEN
BS_COLOR = ORANGE
HP_COLOR = PURPLE
EVCS_COLOR = YELLOW
RESIDUAL_LOAD_COLOR = LIGHT_BLUE
UNKNOWN_COLOR = GREY
FLEX_MAX = BLUE
FLEX_MIN = GREEN
FLEX_REF = YELLOW


def set_style(style: str = "whitegrid", context: str = "notebook"):
    sns.set_style("whitegrid")
    sns.set_context("notebook")


def get_label_and_color(sp_type: EntitiesEnum):
    if sp_type == SystemParticipantsEnum.LOAD:
        return "Load", LOAD_COLOR
    elif sp_type == SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT:
        return "PV", PV_COLOR
    elif sp_type == SystemParticipantsEnum.STORAGE:
        return "Battery", BS_COLOR
    elif sp_type == SystemParticipantsEnum.EV_CHARGING_STATION:
        return "EV Charging Station", EVCS_COLOR
    elif sp_type == SystemParticipantsEnum.ELECTRIC_VEHICLE:
        return "Electric Vehicle", EVCS_COLOR
    elif sp_type == SystemParticipantsEnum.HEATP_PUMP:
        return "Heat Pump", HP_COLOR
    elif sp_type == SystemParticipantsEnum.ENERGY_MANAGEMENT:
        return "Energy Management", LOAD_COLOR
    elif sp_type == SystemParticipantsEnum.PARTICIPANTS_SUM:
        return "Participants Sum", LOAD_COLOR
    else:
        return sp_type, UNKNOWN_COLOR


def get_label_and_color_dict(sp_type: EntitiesEnum):
    label, color = get_label_and_color(sp_type)
    return {"label": label, "color": color}


# === FIGURE DEFAULTS ===

FIGSIZE = (12, 5)
FIGSIZE_WIDE = (15, 5)
SUBPLOTS_PADDING = 10

# === FONT DEFAULTS ===

TITLE_FONT_SIZE = 14

# === SPACING ===

TITLE_PAD = 15

# === SHADING ===

FILL_ALPHA = 0.2


def save_fig(figure: Figure, path: str, file_name: str, format="svg"):
    figure.savefig(os.path.join(path, file_name), bbox_inches="tight", format=format)


def plot_resample(res: Series, hourly_mean: bool):
    return (
        res.resample("60S").ffill()
        if not hourly_mean
        else hourly_mean_resample(res).resample("60S").ffill()
    )


def set_date_format_and_label(ax: Axes, resolution: str):
    date_format, x_label = _date_format_and_x_label(resolution)
    ax.set_xlabel(x_label)
    if resolution == "y":
        # set x labels for every month
        locator = mdates.MonthLocator()
        ax.get_xaxis().set_major_locator(locator)
    if resolution == "m":
        locator = mdates.WeekdayLocator()
        ax.get_xaxis().set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter(date_format))


def _date_format_and_x_label(resolution: str):
    if resolution == "d":
        return "%H:%M", "Time in h"
    elif resolution == "w":
        return "%a", "Day of Week"
    elif resolution == "m":
        return "%x", "Day of Month"
    elif resolution == "y":
        return "%b", "Month"


def set_title(ax: Axes, title: str):
    ax.set_title(title, pad=TITLE_PAD, fontsize=TITLE_FONT_SIZE)


def legend_with_distinct_labels(ax: Axes):
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))


def add_to_kwargs_if_not_exist(kwargs: Dict, to_add: Dict):
    for key, value in to_add.items():
        if key not in kwargs:
            kwargs[key] = value
    return kwargs
