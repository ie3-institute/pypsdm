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
from pypsdm.models.enums import TimeSeriesEnum
from pypsdm.models.ts.types import ComplexPower, ComplexPowerDict


@dataclass(frozen=True)
class TimeSeriesKey:
    ts_uuid: str
    ts_type: TimeSeriesEnum | None

    def __eq__(self, other):
        return self.ts_uuid == other.ts_uuid

    def __hash__(self):
        return hash(self.ts_uuid)


@dataclass
class PrimaryData:
    # ts_key -> ts
    _time_series: ComplexPowerDict[TimeSeriesKey]
    # asset_uuid -> ts_key
    _asset_mapping: dict[str, TimeSeriesKey]

    def __init__(
        self, time_series: "ComplexPowerDict", asset_mapping: dict[str, TimeSeriesKey]
    ):
        self._time_series = time_series
        self._asset_mapping = asset_mapping

    def __eq__(self, other):
        try:
            self.compare(other)
            return True
        except ComparisonError:
            return False

    def __len__(self):
        return len(self._time_series)

    def __contains__(self, uuid):
        if isinstance(uuid, str):
            # Check if it's a time series uuid
            for ts_key in self._time_series.keys():
                if ts_key.ts_uuid == uuid:
                    return True
            # Check if it's an asset uuid
            return uuid in self._asset_mapping
        else:
            return uuid in self._time_series

    def __getitem__(self, get: str | TimeSeriesKey) -> ComplexPower:
        match get:
            case str():
                if get in self._asset_mapping:
                    key = self._asset_mapping[get]
                    return self._time_series[key]
                else:
                    # Look for time series uuid in loaded time series
                    for ts_key in self._time_series.keys():
                        if ts_key.ts_uuid == get:
                            return self._time_series[ts_key]
                    raise KeyError(
                        f"{get} neither a valid time series nor a asset uuid."
                    )
            case TimeSeriesKey():
                return self._time_series[get]
            case _:
                raise ValueError(
                    "Only str uuid of either time series or asset or TimeSeriesKey of time series are allowed as key for PrimaryData."
                )

    def p(self, ffill=True):
        return self._time_series.p(ffill)

    def q(self, ffill=True):
        return self._time_series.q(ffill)

    def p_sum(self) -> Series:
        return self._time_series.p_sum()

    def q_sum(self):
        return self._time_series.q_sum()

    def sum(self) -> ComplexPower:
        return self._time_series.sum()

    def add_time_series(self, ts_key: TimeSeriesKey, ts: ComplexPower, asset: str):
        self._time_series[ts_key] = ts
        self._asset_mapping[asset] = ts_key

    def get_for_assets(self, assets) -> list[ComplexPower]:
        time_series = []
        for asset in assets:
            ts = self.get_for_asset(asset)
            if ts:
                time_series.append(ts)
        return time_series

    def filter_by_assets(self, assets: list[str], skip_missing: bool = False):
        if skip_missing:
            assets = [p for p in assets if p in self._asset_mapping]
        try:
            pm = {p: self._asset_mapping[p] for p in assets}
            ts = ComplexPowerDict(
                {ts_key: self._time_series[ts_key] for ts_key in pm.values()}
            )
            return PrimaryData(ts, pm)
        except KeyError as e:
            missing_key = e.args[0]
            raise KeyError(
                f"Asset with uuid: {missing_key} has no associated primary data."
            ) from e

    def get_for_asset(self, asset: str) -> ComplexPower | None:
        ts_key = self._asset_mapping.get(asset)
        if ts_key:
            return self._time_series[ts_key]
        else:
            return None

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        ts = self._time_series.filter_by_date_time(time)
        return PrimaryData(ts, self._asset_mapping)

    def interval(self, start: datetime, end: datetime):
        ts = self._time_series.interval(start, end)
        return PrimaryData(ts, self._asset_mapping)

    def to_csv(self, path: str, mkdirs=False, delimiter=","):
        write_ts = partial(PrimaryData._write_ts_df, path, mkdirs, delimiter)

        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(write_ts, ts, key)
                for key, ts in list(self._time_series.items())
            ]

            for future in concurrent.futures.as_completed(futures):
                maybe_exception = future.result()
                if isinstance(maybe_exception, Exception):
                    raise maybe_exception

        # write mapping data
        index = [str(uuid.uuid4()) for _ in range(len(self._asset_mapping))]
        mapping_data = pd.DataFrame(
            {
                "asset": self._asset_mapping.keys(),
                "time_series": [
                    ts_key.ts_uuid for ts_key in self._asset_mapping.values()
                ],
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
    def _write_ts_df(
        path: str,
        mkdirs: bool,
        delimiter: str,
        ts: ComplexPower,
        key: TimeSeriesKey,
    ) -> None | Exception:
        try:
            data = copy.deepcopy(ts.data)
            if not isinstance(key.ts_type, TimeSeriesEnum):
                raise ValueError(
                    f"Expected entity type to be TypeSeriesEnum but is {key.ts_type}. Can not determine file name."
                )
            ts_name = key.ts_type.get_csv_input_file_name(key.ts_uuid)
            df_to_csv(
                data,
                path,
                ts_name,
                mkdirs=mkdirs,
                delimiter=delimiter,
                index_label="time",
            )
            return None
        except Exception as e:
            return e

    def compare(self, other):
        if not isinstance(other, type(self)):
            raise ComparisonError(
                f"Type of self {type(self)} != type of other {type(other)}"
            )

        errors = []

        # Compare asset mapping
        asset_ts_self = set([(p, t.ts_uuid) for p, t in self._asset_mapping.items()])
        asset_ts_other = set([(p, t.ts_uuid) for p, t in other._asset_mapping.items()])
        mapping_differences = asset_ts_self.symmetric_difference(asset_ts_other)

        if mapping_differences:
            errors.append(
                ComparisonError(
                    f"Differences in asset mapping. Following entries not in both dicts: {mapping_differences}"
                )
            )

        # Compare time series
        try:
            self._time_series.compare(other._time_series)
        except ComparisonError as e:
            errors.extend(e.differences)

        if errors:
            raise ComparisonError(
                f"Found Differences in {type(self)} comparison: ", differences=errors
            )

    @classmethod
    def from_csv(cls, path: str | Path, delimiter: str | None = None):
        from pypsdm.models.ts.types import ComplexPowerDict

        # get all files that start with "its_"
        path = Path(path).resolve()
        ts_files = [file for file in os.listdir(path) if file.startswith("its_p")]

        time_series_dict = {}

        if ts_files:
            ts_mapping = utils.read_csv(str(path), "time_series_mapping.csv", delimiter)

            asset_mapping_raw = (
                ts_mapping[["asset", "time_series"]]
                .set_index("asset")
                .to_dict()["time_series"]
            )

            pa_read_time_series = partial(
                PrimaryData._read_pd_time_series, path, delimiter=delimiter
            )

            # TODO: Only parallel reading if a lot of ts files
            with concurrent.futures.ProcessPoolExecutor() as executor:
                time_series = executor.map(pa_read_time_series, ts_files)
                for ts_key, ts in time_series:
                    time_series_dict[ts_key] = ts

            asset_mapping = {}
            for asset, ts_uuid in asset_mapping_raw.items():
                # Find the corresponding TimeSeriesKey from the loaded time series
                ts_key = next(
                    (key for key in time_series_dict.keys() if key.ts_uuid == ts_uuid),
                    None,
                )
                if ts_key:
                    asset_mapping[asset] = ts_key

            time_series = ComplexPowerDict(time_series_dict)

            return PrimaryData(time_series, asset_mapping)

        else:
            logger.debug(f"No primary data in path {path}")
            return PrimaryData(
                ComplexPowerDict.empty(),
                dict(),
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
            data = utils.read_csv(dir_path, ts_file, delimiter)
            data["time"] = data["time"].apply(
                lambda date_string: to_date_time(date_string)
            )
            data = data.set_index("time", drop=True)
            if "q" not in data.columns:
                data["q"] = 0
            return TimeSeriesKey(ts_uuid, TimeSeriesEnum(ts_type)), ComplexPower(data)

        else:
            raise IOError(
                f"Could not read time series with name {ts_file}. Expected format: e.g. its_p_5022a70e-a58f-4bac-b8ec-1c62376c216b.csv"
            )

    @classmethod
    def create_empty(cls):
        return cls(ComplexPowerDict.empty(), dict())
