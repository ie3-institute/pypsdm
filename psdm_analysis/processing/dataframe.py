from datetime import datetime

import pandas as pd
from pandas import DataFrame


def divide_positive_negative(df: DataFrame):
    positive = df.copy()
    positive[positive < 0] = 0
    negative = df.copy()
    negative[negative > 0] = 0
    return positive, negative


def join_dataframes(dfs: [DataFrame]):
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
