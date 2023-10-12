import seaborn as sns
from matplotlib import pyplot as plt


def set_sns_style(style: str = "whitegrid", context: str = "notebook"):
    sns.set_style(style)
    sns.set_context(context)


def set_gruvbox_minor_dark_hard():
    dark_tick_color = "#838077"
    tick_color = "#EEEBE1"
    background_color = "#1d2021"
    custom_params = {
        "figure.facecolor": background_color,
        "figure.dpi": 300,
        "figure.figsize": [12, 4],
        "axes.facecolor": background_color,
        "axes.edgecolor": background_color,
        "axes.labelcolor": tick_color,
        "axes.titlecolor": tick_color,
        "xtick.color": tick_color,
        "ytick.color": tick_color,
        "axes.grid": True,
        "grid.color": dark_tick_color,
        "grid.linestyle": "--",
        "grid.linewidth": 0.5,
        "legend.facecolor": background_color,
        "legend.edgecolor": tick_color,
        "legend.labelcolor": tick_color,
        "text.color": tick_color,
    }

    plt.rcParams.update(custom_params)
