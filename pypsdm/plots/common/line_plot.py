import logging

from matplotlib.axes import Axes
from pandas import Series

from pypsdm.models.enums import EntitiesEnum
from pypsdm.plots.common.utils import (
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
    if set_x_label:
        set_date_format_and_label(ax, resolution)
    try:
        res = plot_resample(res, hourly_mean)
    except TypeError as e:
        logging.warn(
            f"Could not resample time series. Plotting without resampling. Error: {e}"
        )
    ax.plot(res, **kwargs)
    if fill_from_index:
        ax.fill_between(res.index, res, alpha=FILL_ALPHA, color=kwargs["color"])
    elif fill_between is not None:
        ax.fill_between(
            res.index,
            plot_resample(fill_between, hourly_mean),
            res,
            alpha=FILL_ALPHA,
            color=kwargs["color"],
        )
    return ax
