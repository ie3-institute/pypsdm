import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

ROOT_DIR = os.path.abspath(__file__ + "/../../../")


def get_absolute_path(path: str):
    if path.startswith(ROOT_DIR):
        return path
    else:
        return Path(ROOT_DIR).joinpath(path)


def get_file_path(path: str, file_name: str):
    if path.startswith(ROOT_DIR):
        return Path(path).joinpath(file_name)
    else:
        return Path(ROOT_DIR).joinpath(path).joinpath(file_name)


def read_csv(path: str, file_name: str, delimiter: str) -> DataFrame:
    full_path = get_file_path(path, file_name)
    if not full_path.exists():
        raise IOError("File with path: " + str(full_path) + " does not exist")
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
    year = int(zoned_date_time[0:4])
    month = int(zoned_date_time[5:7])
    day = int(zoned_date_time[8:10])
    hour = int(zoned_date_time[11:13])
    minute = int(zoned_date_time[14:16])
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
    df: DataFrame, path: str, file_name: str, mkdirs=True, delimiter: str = ","
):
    file_path = get_file_path(path, file_name)
    if mkdirs:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    df = df.replace(True, "true")
    df = df.replace(False, "false")
    df = df.sort_index()
    df.to_csv(file_path, index=True, index_label="uuid", sep=delimiter)
