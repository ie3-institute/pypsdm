import concurrent.futures
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from functools import partial

from psdm_analysis.io import utils
from psdm_analysis.io.utils import to_date_time
from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.result.power import PQResult


@dataclass
class PrimaryData:
    name: str
    # ts_uuid -> ts
    time_series: dict[str, PQResult]
    # participant_uuid -> ts_uuid
    participant_mapping: dict[str, str]

    def get_for_participant(self, participant: str):
        time_series_id = self.participant_mapping[participant]
        return self.time_series[time_series_id]

    def get_for_participants(self, participants):
        time_series = []
        for participant in participants:
            if participant in self.participant_mapping:
                time_series.append(self.get_for_participant(participant))
        return time_series

    def filter_for_time_interval(self, start: datetime, end: datetime):
        filtered_time_series = {
            uuid: time_series.filter_for_time_interval(start, end)
            for uuid, time_series in self.time_series.items()
        }
        return PrimaryData(self.name, filtered_time_series, self.participant_mapping)

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

            pa_read_time_series = partial(PrimaryData.read_time_series, path, delimiter)

            with concurrent.futures.ProcessPoolExecutor() as executor:
                time_series = executor.map(pa_read_time_series, ts_files)
                for ts in time_series:
                    time_series_dict[ts.name] = ts

            return PrimaryData("Primary Data", time_series_dict, participant_mapping)

        else:
            logging.debug(f"No primary data in path {path}")
            return PrimaryData("Primary Data", dict(), dict())

    @staticmethod
    def read_time_series(dir_path: str, delimiter: str, ts_file: str):
        name = ts_file[-40:][:36]
        data = utils.read_csv(str(dir_path), ts_file, delimiter)
        data["time"] = data["time"].apply(lambda date_string: to_date_time(date_string))
        data = data.set_index("time")
        if "q" not in data.columns:
            data["q"] = 0
        return PQResult(SystemParticipantsEnum.PRIMARY_DATA, name, name, data)
