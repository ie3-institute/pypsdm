import concurrent.futures
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from typing import Union

import pandas as pd
from pandas import Series

from psdm_analysis.io import utils
from psdm_analysis.io.utils import to_date_time
from psdm_analysis.models.enums import SystemParticipantsEnum
from psdm_analysis.models.result.power import PQResult


@dataclass
class PrimaryData:
    # ts_uuid -> ts
    time_series: dict[str, PQResult]
    # participant_uuid -> ts_uuid
    participant_mapping: dict[str, str]

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
        ts_uuid = ts_file[-40:][:36]
        data = utils.read_csv(str(dir_path), ts_file, delimiter)
        data["time"] = data["time"].apply(lambda date_string: to_date_time(date_string))
        data = data.set_index("time")
        if "q" not in data.columns:
            data["q"] = 0
        return PQResult(SystemParticipantsEnum.PRIMARY_DATA, ts_uuid, ts_uuid, data)

    @classmethod
    def create_empty(cls):
        return cls(dict(), dict())
