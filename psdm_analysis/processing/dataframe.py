from datetime import datetime

import pandas as pd
from pandas import DataFrame
from polars.testing import assert_frame_equal

import polars as pl


def divide_positive_negative(df: DataFrame):
    """
    Divide a dataframe into two dataframes, one containing only positive values and one
    containing only negative values. All other values are set to 0.
    """

    positive = df.copy()
    positive[positive < 0] = 0
    negative = df.copy()
    negative[negative > 0] = 0
    return positive, negative


def divide_positive_negative_pl(df: pl.DataFrame):
    """
    Divide a dataframe into two dataframes, one containing only positive values and one
    containing only negative values. All other values are set to 0.
    """
    # TODO: compute benchmark against pandas version
    neg = df.select(
        [
            pl.when(pl.col(col).lt(0)).then(pl.lit(0)).otherwise(pl.col(col)).alias(col)
            for col in df.columns
        ]
    )
    pos = df.select(
        [
            pl.when(pl.col(col).gt(0)).then(pl.lit(0)).otherwise(pl.col(col)).alias(col)
            for col in df.columns
        ]
    )

    return pos, neg


def join_dataframes(dfs: list[DataFrame]):
    return pd.concat(dfs)


def filter_data_for_time_interval(
    data: DataFrame, start: datetime, end: datetime
) -> DataFrame:
    if data.empty:
        return data
    if not data.index.is_monotonic_increasing:
        data = data.sort_index()
    # we want the first value to be start if present and if not the last value before start
    all_after_start = (data.index > start).all()
    all_after_end = (data.index >= end).all()
    if all_after_start and all_after_end:
        return data.drop(data.index)
    elif all_after_start:
        start_row = data.index[1]
    else:
        before_start = data.index[data.index <= start]
        start_row = before_start[-1]
    # since this is the start of the time interval
    end_row = data.index[data.index <= end][-1]
    filtered_data = data[start_row:end_row]
    return filtered_data.rename(index={filtered_data.loc[start_row].name: start})


def filter_data_for_time_interval_pl(data, start, end):
    data = data.sort("time")
    between = data.filter(pl.col("time").is_between(start, end))
    between_start = between[0, "time"]
    between_end = between[-1, "time"]
    # since we are dealing with discrete event time series:
    # if the exact start timestamp is not present, the state of the time series
    # is still the same as the last state before the start timestamp ()
    if between_start > start:
        before = data.filter(pl.col("time").lt(start))
        last_before_state = before[-1].clone()
        last_before_state[0, "time"] = [start]
        between = pl.concat([last_before_state, between])
    # the end state of the time series is the last state before the end timestamp
    # if the exact end timestamp is not present within the time series
    if between_end < end:
        after = data.filter(pl.col("time").gt(end))
        last_after_state = after[0].clone()
        last_after_state[0, "time"] = [end]
        between = pl.concat([between, last_after_state])
    return between


def compare_dfs(a: DataFrame, b: DataFrame, check_like=True, **kwargs):
    pd.testing.assert_frame_equal(
        a,
        b,
        check_like=check_like,
        check_column_type=False,
        check_index_type=False,
        **kwargs,
    )


def compare_dfs_pl(a: pl.DataFrame, b: pl.DataFrame, **kwargs):
    assert_frame_equal(a, b, check_column_order=False, **kwargs)
