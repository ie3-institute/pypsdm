from datetime import datetime

import pandas as pd
from pandas import DataFrame

from pypsdm.processing.numba import add_2d_array


def add_df(a: pd.DataFrame, b: pd.DataFrame):
    """
    Adds two dataframes with different indices in an event discrete manner.
    """
    if not a.columns.equals(b.columns):
        diff = set(a.columns).symmetric_difference(set(b.columns))
        raise ValueError(
            f"DataFrames have different columns: {diff} not in both DataFrames."
        )

    if len(a) == 0:
        return b
    if len(b) == 0:
        return a

    b = b.reindex(columns=a.columns)
    if not a.index.is_monotonic_increasing:
        a.sort_index(inplace=True)
    if not b.index.is_monotonic_increasing:
        b.sort_index(inplace=True)

    a = a.astype({col: "float64" for col in a.select_dtypes(include="int").columns})
    b = b.astype({col: "float64" for col in b.select_dtypes(include="int").columns})

    index = a.index.union(b.index)
    values = add_2d_array(
        index.to_numpy(),
        a.index.to_numpy(),
        b.index.to_numpy(),
        a.values,
        b.values,  # type: ignore
    )
    return pd.DataFrame(values, index=index, columns=a.columns)  # type: ignore


def divide_positive_negative(df: DataFrame):
    positive = df.copy()
    positive[positive < 0] = 0
    negative = df.copy()
    negative[negative > 0] = 0
    return positive, negative


def filter_data_for_time_interval(
    data: DataFrame, start: datetime, end: datetime
) -> DataFrame:
    if data.empty:
        return data
    if not data.index.is_monotonic_increasing:
        data = data.sort_index()

    # Remove time zone to make datetime objects comparable
    if start.tzinfo is not None:
        start = start.replace(tzinfo=None)
    if end.tzinfo is not None:
        end = end.replace(tzinfo=None)

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


def compare_dfs(a: DataFrame, b: DataFrame, check_like=True, **kwargs):
    # compare columns
    a_cols = set(a.columns)
    b_cols = set(b.columns)

    a_diff = a_cols - b_cols
    if a_diff:
        raise AssertionError(f"Columns: {a_diff} in left but not in right")
    b_diff = b_cols - a_cols
    if b_diff:
        raise AssertionError(f"Columns: {b_diff} in right but not in left")

    pd.testing.assert_frame_equal(
        a,
        b,
        check_like=check_like,
        check_column_type=False,
        check_index_type=False,
        **kwargs,
    )
