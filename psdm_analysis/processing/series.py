import pandas as pd
from pandas import DataFrame, Series


def duration_weighted_series(series: Series):
    values = series[:-1].reset_index(drop=True)
    time = (
        (series.index[1::] - series.index[:-1])
        .to_series()
        .apply(lambda x: x.total_seconds() / 3600)
        .reset_index(drop=True)
    )
    return pd.concat([values.rename("values"), time.rename("time")], axis=1)


def weighted_series_sum(weighted_series: DataFrame) -> float:
    return (weighted_series["values"] * weighted_series["time"]).sum()


def duration_weighted_sum(series: Series) -> float:
    weighted_series = duration_weighted_series(series)
    return weighted_series_sum(weighted_series)


def add_series(this: Series, that: Series, name: str) -> Series:
    # todo: Is there a more performant implementation?
    return (
        this.to_frame()
        .join(that.rename("other"), how="outer")
        .fillna(method="ffill")
        .sum(axis=1)
        .rename(name)
    )


def join_series(series: [Series]) -> DataFrame:
    first_series = series[0]
    df = first_series.rename(first_series.name).to_frame()
    for series in series[1:]:
        df = df.join(series.rename(series.name), how="outer").fillna(method="ffill")
    return df


def hourly_mean_resample(series: Series) -> Series:
    return series.resample("60s").ffill().resample("1h").mean()


def load_and_generation(p_ts: Series) -> (float, float):
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
