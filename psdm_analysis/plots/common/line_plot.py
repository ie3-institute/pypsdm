import datetime

from matplotlib.axes import Axes
from pandas import Series

from psdm_analysis.models.input.enums import EntitiesEnum
from psdm_analysis.plots.common.utils import (
    FILL_ALPHA,
    add_to_kwargs_if_not_exist,
    get_label_and_color_dict,
    plot_resample,
    set_date_format_and_label,
)


def ax_plot_time_series(
    ax: Axes,
    res: Series,
    type: EntitiesEnum,
    resolution: str,
    hourly_mean: bool = False,
    fill_from_index=False,
    fill_between=None,
    set_x_label: bool = True,
    **kwargs,
):
    args = get_label_and_color_dict(type)
    kwargs = add_to_kwargs_if_not_exist(kwargs, args)

    ts = plot_resample(res, hourly_mean)
    if resolution == "auto":
        if ts.index.max()-ts.index.min() <= datetime.timedelta(days=4):
            used_resolution = "d"
        elif ts.index.max()-ts.index.min() <= datetime.timedelta(days=30):
            used_resolution = "w"
        elif ts.index.max()-ts.index.min() <= datetime.timedelta(days=60):
            used_resolution = "m"
        else:
            used_resolution = "y"
    else:
        used_resolution = resolution
    if set_x_label:
        set_date_format_and_label(ax, used_resolution)

    ax.plot(ts, **kwargs)

    if fill_from_index:
        ax.fill_between(ts.index, ts, alpha=FILL_ALPHA, color=kwargs["color"])
    elif fill_between is not None:
        ax.fill_between(
            ts.index,
            plot_resample(fill_between, hourly_mean),
            ts,
            alpha=FILL_ALPHA,
            color=kwargs["color"],
        )

    return ax
