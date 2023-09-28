from typing import Tuple

import pandas as pd
from pandas import DataFrame, Series

import polars as pl
from psdm_analysis.io.utils import TIME_INDEX_COL


def duration_weighted_series(series: Series):
    series.sort_index(inplace=True)
    values = series[:-1].reset_index(drop=True)
    time = (
        (series.index[1::] - series.index[:-1])
        .to_series()
        .apply(lambda x: x.total_seconds() / 3600)
        .reset_index(drop=True)
    )
    return pd.concat([values.rename("values"), time.rename("time")], axis=1)


def duration_weighted_sum_pl(
    data: pl.DataFrame, target_col: str, time_col: str = TIME_INDEX_COL
):
    duration = data.select(
        pl.col(time_col).shift(-1).sub(pl.col(time_col)).fill_null(0)
    ) / (
        3600 * 1e6
    )  # ns to h
    return data.select(pl.col(target_col).mul(duration)).sum()


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


def add_series_pl(this: pl.DataFrame, that: pl.DataFrame, name: str):
    # TODO: Is there a more performant implementation?
    assert "time" in this.columns and "time" in that.columns, "Time column missing"
    joined = this.join(that, on="time", how="outer").sort("time")
    ffill = joined.select(pl.col("time"), pl.all().exclude("time").forward_fill())
    return ffill.select(
        pl.col("time"), ffill.select(pl.all().exclude("time")).sum(axis=1)
    )


def join_series(series: list[Series]) -> DataFrame:
    first_series = series[0]
    df = first_series.rename(first_series.name).to_frame()
    for series in series[1:]:
        df = df.join(series.rename(series.name), how="outer").fillna(method="ffill")
    return df


def hourly_mean_resample(series: Series) -> Series:
    return series.resample("60s").ffill().resample("1h").mean()


def load_and_generation(p_ts: Series) -> Tuple[float, float]:
    weighted_series = duration_weighted_series(p_ts)
    load_filter = weighted_series["values"] > 0
    weighted_load = weighted_series[load_filter]
    weighted_generation = weighted_series[~load_filter]
    return (
        weighted_series_sum(weighted_load),
        weighted_series_sum(weighted_generation),
    )


def load_and_generation_pl(
    p_ts: pl.DataFrame, time_index=TIME_INDEX_COL
) -> Tuple[float, float]:
    # TODO: P_INDEX
    data = p_ts.with_columns(
        pl.col(time_index).shift(-1).fill_null(0).alias("duration")
        / (3600 * 1e6)  # ns to h
    ).select(
        pl.when(pl.col("p").gt(0))
        .then(pl.col("p"))
        .otherwise(pl.lit(0))
        .mul(pl.col("duration"))
        .alias("load"),
        pl.when(pl.col("p").lt(0))
        .then(pl.col("p"))
        .otherwise(pl.lit(0))
        .mul(pl.col("duration"))
        .alias("generation"),
    )
    return data.select(pl.col("load")).item(), data.select(pl.col("generation")).item()
    # loads = p_ts.filter()


def divide_positive_negative_pl(
    df: pl.DataFrame, index_col="time"
) -> tuple[pl.DataFrame, pl.DataFrame]:
    cols = [col for col in df.columns if col != index_col]
    neg = df.select(
        [
            pl.col(index_col),
            *[
                pl.when(pl.col(col).lt(0))
                .then(pl.lit(0))
                .otherwise(pl.col(col))
                .alias(col)
                for col in cols
            ],
        ]
    )
    pos = df.select(
        [
            pl.col(index_col),
            *[
                pl.when(pl.col(col).gt(0))
                .then(pl.lit(0))
                .otherwise(pl.col(col))
                .alias(col)
                for col in cols
            ],
        ]
    )
    return pos, neg


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
