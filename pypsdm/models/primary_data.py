import concurrent.futures
import copy
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Union

import pandas as pd
from loguru import logger
from pandas import Series

from pypsdm.errors import ComparisonError
from pypsdm.io import utils
from pypsdm.io.utils import df_to_csv, to_date_time
from pypsdm.models.enums import SystemParticipantsEnum, TimeSeriesEnum
from pypsdm.models.result.participant.pq_dict import PQResultDict
from pypsdm.models.result.power import PQResult


@dataclass
class PrimaryData:
    # ts_uuid -> ts
    time_series: "PQResultDict"
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
        return uuid in self.time_series or uuid in self.participant_mapping

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
                    logger.warning("Step is not supported for slicing. Ignoring it.")
                if not (isinstance(start, datetime) and isinstance(stop, datetime)):
                    raise ValueError("Only datetime slicing is supported")
                return self.filter_for_time_interval(start, stop)
            case _:
                raise ValueError(
                    "Only get by uuid or datetime slice for filtering is supported."
                )

    def p(self, ffill=True):
        return self.time_series.p(ffill)

    def q(self, ffill=True):
        return self.time_series.q(ffill)

    def p_sum(self) -> Series:
        return self.time_series.p_sum()

    def q_sum(self):
        return self.time_series.q_sum()

    def sum(self) -> PQResult:
        return self.time_series.sum()

    def get_for_participants(self, participants) -> list[PQResult]:
        time_series = []
        for participant in participants:
            ts = self.get_for_participant(participant)
            if ts:
                time_series.append(ts)
        return time_series

    def filter_by_participants(
        self, participants: list[str], skip_missing: bool = False
    ):
        if skip_missing:
            participants = [p for p in participants if p in self.participant_mapping]
        try:
            pm = {p: self.participant_mapping[p] for p in participants}
            ts = {ts_uuid: self.time_series[ts_uuid] for ts_uuid in pm.values()}
            return PrimaryData(ts, pm)
        except KeyError as e:
            missing_key = e.args[0]
            raise KeyError(
                f"Participant with uuid: {missing_key} has no associated primary data."
            ) from e

    def get_for_participant(self, participant: str) -> PQResult | None:
        ts_uuid = self.participant_mapping.get(participant)
        if ts_uuid:
            return self.time_series.entities[ts_uuid]
        else:
            return None

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        """
        Filters the result by the given datetime or list of datetimes.
        :param time: the time or list of times to filter by
        :return: a new result containing only the given time or times
        """
        ts = self.time_series.filter_by_date_time(time)
        return PrimaryData(ts, self.participant_mapping)

    def filter_for_time_interval(self, start: datetime, end: datetime):
        ts = self.time_series.filter_for_time_interval(start, end)
        return PrimaryData(ts, self.participant_mapping)

    def to_csv(self, path: str, mkdirs=False, delimiter=","):
        write_ts = partial(PrimaryData._write_ts_df, path, mkdirs, delimiter)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            executor.map(write_ts, list(self.time_series.entities.values()))

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
        try:
            self.time_series.compare(other.time_series)
        except ComparisonError as e:
            errors.extend(e.differences)

        if errors:
            raise ComparisonError(
                f"Found Differences in {type(self)} comparison: ", differences=errors
            )

    @classmethod
    def from_csv(cls, path: str | Path, delimiter: str | None = None):
        from pypsdm.models.result.participant.pq_dict import PQResultDict

        # get all files that start with "its_"
        path = Path(path).resolve()
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
                PrimaryData._read_pd_time_series, path, delimiter=delimiter
            )

            # TODO: Only parallel reading if a lot of ts files
            with concurrent.futures.ProcessPoolExecutor() as executor:
                time_series = executor.map(pa_read_time_series, ts_files)
                for ts in time_series:
                    time_series_dict[ts.name] = ts

            time_series = PQResultDict(
                SystemParticipantsEnum.PRIMARY_DATA, time_series_dict
            )

            return PrimaryData(time_series, participant_mapping)

        else:
            logger.debug(f"No primary data in path {path}")
            return PrimaryData(
                PQResultDict.create_empty(SystemParticipantsEnum.PRIMARY_DATA), dict()
            )

    @staticmethod
    def _read_pd_time_series(
        dir_path: Path | str, ts_file: str, delimiter: str | None = None
    ):
        ts_types = "|".join([e.value for e in TimeSeriesEnum])
        pattern = (
            f"({ts_types})_"
            + r"([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}).csv"  # uuid4 regex
        )
        match = re.match(pattern, ts_file)
        if match:
            ts_type, ts_uuid = match.groups()
            data = utils.read_csv(dir_path, ts_file, delimiter, index_col="uuid")
            data["time"] = data["time"].apply(
                lambda date_string: to_date_time(date_string)
            )
            data = data.set_index("time", drop=True)
            if "q" not in data.columns:
                data["q"] = 0
            return PQResult(TimeSeriesEnum(ts_type), ts_uuid, ts_uuid, data)

        else:
            raise IOError(
                f"Could not read time series with name {ts_file}. Expected format: e.g. its_p_5022a70e-a58f-4bac-b8ec-1c62376c216b.csv"
            )

    @classmethod
    def create_empty(cls):
        return cls(
            PQResultDict.create_empty(SystemParticipantsEnum.PRIMARY_DATA), dict()
        )
