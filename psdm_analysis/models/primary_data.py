import concurrent.futures
import copy
import logging
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from typing import Union

import pandas as pd
from pandas import Series

from psdm_analysis.errors import ComparisonError
from psdm_analysis.io import utils
from psdm_analysis.io.utils import df_to_csv, to_date_time
from psdm_analysis.models.enums import TimeSeriesEnum
from psdm_analysis.models.result.power import PQResult


@dataclass
class PrimaryData:
    # ts_uuid -> ts
    time_series: dict[str, PQResult]
    # participant_uuid -> ts_uuid
    participant_mapping: dict[str, str]

    def __eq__(self, other):
        try:
            self.compare(other)
            return True
        except ComparisonError:
            return False

    def __len__(self):
        return len(self.time_series)

    def __contains__(self, uuid):
        return uuid in self.time_series

    def __getitem__(self, get):
        match get:
            case str():
                if get in self.participant_mapping:
                    return self.time_series[self.participant_mapping[get]]
                elif get in self.time_series:
                    return self.time_series[get]
                else:
                    raise KeyError(
                        f"{get} neither a valid time series nor a participant uuid."
                    )
            case slice():
                start, stop, step = get.start, get.stop, get.step
                if step is not None:
                    logging.warning("Step is not supported for slicing. Ignoring it.")
                if not (isinstance(start, datetime) and isinstance(stop, datetime)):
                    raise ValueError("Only datetime slicing is supported")
                time_series = {
                    key: e.filter_for_time_interval(start, stop)
                    for key, e in self.time_series.items()
                }
                return PrimaryData(time_series, self.participant_mapping)
            case _:
                raise ValueError(
                    "Only get by uuid or datetime slice for filtering is supported."
                )

    @property
    def p(self):
        if not self.time_series.values():
            return None
        return (
            pd.DataFrame({p_uuid: res.p for p_uuid, res in self.time_series.items()})
            .fillna(method="ffill")
            .sort_index()
        )

    @property
    def q(self):
        return (
            pd.DataFrame({p_uuid: res.q for p_uuid, res in self.time_series.items()})
            .fillna(method="ffill")
            .sort_index()
        )

    def p_sum(self) -> Series:
        if not self.time_series:
            return Series(dtype=float)
        return self.p.fillna(method="ffill").sum(axis=1).rename("p_sum")

    def q_sum(self):
        if not self.time_series:
            return Series(dtype=float)
        return self.q.fillna(method="ffill").sum(axis=1).rename("q_sum")

    def sum(self) -> PQResult:
        return PQResult.sum(list(self.time_series.values()))

    def get_for_participant(self, participant: str):
        time_series_id = self.participant_mapping[participant]
        return self.time_series[time_series_id]

    def get_for_participants(self, participants):
        time_series = []
        for participant in participants:
            if participant in self.participant_mapping:
                time_series.append(self.get_for_participant(participant))
        return time_series

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        """
        Filters the result by the given datetime or list of datetimes.
        :param time: the time or list of times to filter by
        :return: a new result containing only the given time or times
        """
        return PrimaryData(
            {uuid: result[time] for uuid, result in self.time_series.items()},
            self.participant_mapping,
        )

    def filter_for_time_interval(self, start: datetime, end: datetime):
        filtered_time_series = {
            uuid: time_series.filter_for_time_interval(start, end)
            for uuid, time_series in self.time_series.items()
        }
        return PrimaryData(filtered_time_series, self.participant_mapping)

    def to_csv(self, path: str, mkdirs=True, delimiter=","):
        write_ts = partial(PrimaryData._write_ts_df, path, mkdirs, delimiter)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            executor.map(write_ts, list(self.time_series.values()))

        # write mapping data
        index = [str(uuid.uuid4()) for _ in range(len(self.participant_mapping))]
        mapping_data = pd.DataFrame(
            {
                "participant": self.participant_mapping.keys(),
                "time_series": self.participant_mapping.values(),
            },
            index=index,
        )
        mapping_data.index.name = "uuid"
        df_to_csv(
            mapping_data,
            path,
            "time_series_mapping.csv",
            delimiter=delimiter,
            index_label="uuid",
        )

    @staticmethod
    def _write_ts_df(path: str, mkdirs: bool, delimiter: str, ts: PQResult):
        data = copy.deepcopy(ts.data)
        if not isinstance(ts.entity_type, TimeSeriesEnum):
            raise ValueError(
                f"Expected entity type to be TypeSeriesEnum but is {ts.entity_type}. Can not determine file name."
            )
        ts_name = ts.entity_type.get_csv_input_file_name(ts.input_model)
        data["uuid"] = [str(uuid.uuid4()) for _ in range(len(ts))]
        data["time"] = data.index
        data.set_index("uuid", inplace=True)
        df_to_csv(
            data,
            path,
            ts_name,
            mkdirs=mkdirs,
            delimiter=delimiter,
            index_label="uuid",
        )

    def compare(self, other):
        if not isinstance(other, type(self)):
            raise ComparisonError(
                f"Type of self {type(self)} != type of other {type(other)}"
            )

        errors = []

        # Compare participant mapping
        participant_ts_self = set([(p, t) for p, t in self.participant_mapping.items()])
        participant_ts_other = set(
            [(p, t) for p, t in other.participant_mapping.items()]
        )
        mapping_differences = participant_ts_self.symmetric_difference(
            participant_ts_other
        )
        if mapping_differences:
            errors.append(
                ComparisonError(
                    f"Differences in participant mapping. Following entries not in both dicts: {mapping_differences}"
                )
            )

        # Compare time series
        ts_self_keys = set(self.time_series.keys())
        ts_other_keys = set(self.time_series.keys())
        ts_differences = ts_self_keys.symmetric_difference(ts_other_keys)
        if ts_differences:
            errors.append(
                ComparisonError(
                    f"Differences in time series keys. Following keys not in both dicts: {ts_differences}"
                )
            )

        for key, ts in self.time_series.items():
            if key in other:
                try:
                    ts.compare(other[key])
                except ComparisonError as e:
                    errors.append(e)

        if errors:
            raise ComparisonError(
                f"Found Differences in {type(self)} comparison: ", errors=errors
            )

    @classmethod
    def from_csv(cls, path: str, delimiter: str):
        # get all files that start with "its_"
        path = utils.get_absolute_path(path)
        ts_files = [file for file in os.listdir(path) if file.startswith("its_p")]

        time_series_dict = {}

        if ts_files:
            ts_mapping = utils.read_csv(str(path), "time_series_mapping.csv", delimiter)

            participant_mapping = (
                ts_mapping[["participant", "time_series"]]
                .set_index("participant")
                .to_dict()["time_series"]
            )

            pa_read_time_series = partial(
                PrimaryData._read_pd_time_series, path, delimiter
            )

            # TODO: Only parallel reading if a lot of ts files
            with concurrent.futures.ProcessPoolExecutor() as executor:
                time_series = executor.map(pa_read_time_series, ts_files)
                for ts in time_series:
                    time_series_dict[ts.name] = ts

            return PrimaryData(time_series_dict, participant_mapping)

        else:
            logging.debug(f"No primary data in path {path}")
            return PrimaryData(dict(), dict())

    @staticmethod
    def _read_pd_time_series(dir_path: str, delimiter: str, ts_file: str):
        ts_types = "|".join([e.value for e in TimeSeriesEnum])
        pattern = (
            f"({ts_types})_"
            + r"([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}).csv"
        )
        match = re.match(pattern, ts_file)
        if match:
            ts_type, ts_uuid = match.groups()
            data = utils.read_csv(str(dir_path), ts_file, delimiter, index_col="uuid")
            data["time"] = data["time"].apply(
                lambda date_string: to_date_time(date_string)
            )
            data = data.set_index("time", drop=True)
            if "q" not in data.columns:
                data["q"] = 0
            return PQResult(TimeSeriesEnum(ts_type), ts_uuid, ts_uuid, data)

        else:
            raise IOError(
                f"Could not read time series with name {ts_file}. Expected format: its_p_5022a70e-a58f-4bac-b8ec-1c62376c216b.csv"
            )

    @classmethod
    def create_empty(cls):
        return cls(dict(), dict())
