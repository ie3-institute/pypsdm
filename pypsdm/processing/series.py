from typing import Tuple

import pandas as pd
from pandas import DataFrame, Series

from pypsdm.processing.numba import add_array


def duration_weighted_series(series: Series):
    series.sort_index(inplace=True)
    values = series[:-1].reset_index(drop=True)
    duration = (
        (series.index[1::] - series.index[:-1])
        .to_series()
        .apply(lambda x: x.total_seconds() / 3600)
        .reset_index(drop=True)
    )
    return pd.concat([values.rename("values"), duration.rename("duration")], axis=1)


def weighted_series_sum(weighted_series: DataFrame) -> float:
    if len(weighted_series) == 0:
        return 0.0
    return (weighted_series["values"] * weighted_series["duration"]).sum()


def duration_weighted_sum(series: Series) -> float:
    weighted_series = duration_weighted_series(series)
    return weighted_series_sum(weighted_series)


def add_series(a: pd.Series, b: pd.Series, name: str | None = None):
    if not a.index.is_monotonic_increasing:
        a.sort_index(inplace=True)
    if not b.index.is_monotonic_increasing:
        b.sort_index(inplace=True)
    index = a.index.union(b.index)
    values = add_array(
        index.to_numpy(), a.index.to_numpy(), b.index.to_numpy(), a.values, b.values  # type: ignore
    )
    return (
        pd.Series(values, index=index)
        if name is None
        else pd.Series(values, index=index, name=name)
    )


def join_series(series: list[Series]) -> DataFrame:
    first_series = series[0]
    df = first_series.rename(first_series.name).to_frame()
    for series in series[1:]:
        df = df.join(series.rename(series.name), how="outer").fillna(method="ffill")
    return df


def hourly_mean_resample(series: Series) -> Series:
    return series.resample("60s").ffill().resample("1h").mean()


def pos_and_neg_area(p_ts: Series) -> Tuple[float, float]:
    """
    Calculate the positive and negative area under the curve of a time series.
    """
    weighted_series = duration_weighted_series(p_ts)
    load_filter = weighted_series["values"] > 0
    weighted_load = weighted_series[load_filter]
    weighted_generation = weighted_series[~load_filter]
    return (
        weighted_series_sum(weighted_load),
        weighted_series_sum(weighted_generation),
    )


def divide_positive_negative(series: Series):
    positive = series.copy(deep=True)
    positive[positive < 0] = 0
    negative = series.copy(deep=True)
    negative[negative > 0] = 0
    return positive, negative


def p_to_pq_frame(p: Series):
    if not p.name == "p":
        p = p.rename("p")
    data = p.to_frame()
    data["q"] = 0
    return data
