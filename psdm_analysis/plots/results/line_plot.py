from matplotlib.axes import Axes
from pandas import Series

from psdm_analysis.models.input.enums import EntitiesEnum
from psdm_analysis.plots.utils import (
    FILL_ALPHA,
    add_to_kwargs_if_not_exist,
    get_label_and_color,
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
    **kwargs,
):
    args = get_label_and_color_dict(type)
    kwargs = add_to_kwargs_if_not_exist(kwargs, args)
    set_date_format_and_label(ax, resolution)
    ts = plot_resample(res, hourly_mean)
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
