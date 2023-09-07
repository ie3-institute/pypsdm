import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Union

import pandas as pd
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

ROOT_DIR = os.path.abspath(__file__ + "/../../../")


class DateTimePattern(Enum):
    UTC_TIME_PATTERN_EXTENDED = "%Y-%m-%dT%H:%M:%SZ"
    UTC_TIME_PATTERN = "%Y-%m-%dT%H:%MZ"
    PLAIN = "%Y-%m-%d %H:%M:%S"


def get_absolute_path_from_project_root(path: str):
    if not isinstance(path, str):
        path = str(path)
    if path.startswith(ROOT_DIR):
        return path
    else:
        return Path(ROOT_DIR).joinpath(path)


def get_absolute_path_from_working_dir(path: str | Path) -> Path:
    """
    Given a path (as string or pathlib.Path), returns its absolute path based on
    the current working directory. If the path is already absolute, it's returned unchanged.

    Args:
    - path (Union[str, Path]): The input path.

    Returns:
    - Path: The absolute path as a pathlib.Path object.
    """
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj
    return path_obj.resolve()


def get_file_path(path: str | Path, file_name: str):
    return Path(path).resolve().joinpath(file_name)


def read_csv(
    path: str | Path, file_name: str, delimiter: str, index_col: Optional[str] = None
) -> DataFrame:
    full_path = get_file_path(path, file_name)
    if not full_path.exists():
        raise IOError("File with path: " + str(full_path) + " does not exist")
    if index_col:
        return pd.read_csv(
            full_path, delimiter=delimiter, quotechar='"', index_col=index_col
        )
    else:
        return pd.read_csv(full_path, delimiter=delimiter, quotechar='"')


def to_date_time(zoned_date_time: str) -> datetime:
    """
    Converts zoned date time string with format: "yyyy-MM-dd'T'HH:mm:ss[.S[S][S]]'Z'"
    e.g. '2022-02-01T00:15Z[UTC]' to python datetime

    Args:
        zoned_date_time: The zoned date time string to convert.

    Returns:
        The converted datetime object.
    """
    if not zoned_date_time or not isinstance(zoned_date_time, str):
        raise ValueError(f"Unexpected date time string: {zoned_date_time}")
    try:
        year = int(zoned_date_time[0:4])
        month = int(zoned_date_time[5:7])
        day = int(zoned_date_time[8:10])
        hour = int(zoned_date_time[11:13])
        minute = int(zoned_date_time[14:16])
    except IndexError:
        raise IOError(f"Could not parse time stamp: {zoned_date_time}")
    return datetime(year=year, month=month, day=day, hour=hour, minute=minute)


def csv_to_grpd_df(
    file_name: str, simulation_data_path: str, delimiter: str
) -> DataFrameGroupBy:
    """
    Reads in a PSDM csv results file cleans it up and groups it by input_archive model.

    Args:
        file_name: name of the file to read
        simulation_data_path: base directory of the result data
        delimiter: the csv delimiter

    Returns:
        DataFrameGroupBy object of the file
    """
    data = read_csv(simulation_data_path, file_name, delimiter)

    if "uuid" in data.columns:
        data = data.drop(columns=["uuid"])
    return data.groupby(by="input_model")


def check_filter(filter_start: Optional[datetime], filter_end: Optional[datetime]):
    if (filter_start or filter_end) and not (filter_start and filter_end):
        raise ValueError(
            "Both start and end of the filter must be provided if one is provided."
        )
    if (filter_start and filter_end) and (filter_start > filter_end):
        raise ValueError("Filter start must be before end.")


def df_to_csv(
    df: DataFrame,
    path: Union[str, Path],
    file_name: str,
    mkdirs=True,
    delimiter: str = ",",
    index_label="uuid",
    datetime_pattern=DateTimePattern.UTC_TIME_PATTERN,
):
    df = df.copy(deep=True)
    if isinstance(path, Path):
        path = str(path)
    file_path = get_file_path(path, file_name)
    if mkdirs:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    bool_cols = []
    for col in df.columns:
        is_bool_col = df[col].dropna().map(type).eq(bool).all()
        if is_bool_col:
            bool_cols.append(col)

    # replace True with 'true' only in boolean columns
    df[bool_cols] = df[bool_cols].replace({True: "true", False: "false"})

    if isinstance(df.index, pd.DatetimeIndex):
        df.index = df.index.strftime(datetime_pattern.value)

    datetime_cols = df.select_dtypes(
        include=["datetime64[ns, UTC]", "datetime64"]
    ).columns
    for col in datetime_cols:
        df[col] = df[col].apply(
            lambda x: x.strftime(datetime_pattern.value) if not pd.isnull(x) else x
        )

    df.to_csv(file_path, index=True, index_label=index_label, sep=delimiter)


def bool_converter(maybe_bool):
    if isinstance(maybe_bool, bool):
        return maybe_bool
    elif isinstance(maybe_bool, str) and maybe_bool.lower() in ["true", "false"]:
        return maybe_bool.lower() == "true"
    else:
        raise ValueError("Cannot convert to bool: " + str(maybe_bool))
