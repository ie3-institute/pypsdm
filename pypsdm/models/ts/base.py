import copy
from abc import ABC
from collections import UserDict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Self, Tuple, Type, TypeVar, Union

import pandas as pd
from loguru import logger
from pandas import DataFrame, Series
from pandas.errors import ParserError

from pypsdm.errors import ComparisonError
from pypsdm.io.utils import to_date_time
from pypsdm.processing.dataframe import compare_dfs, filter_data_for_time_interval

pd.set_option("mode.copy_on_write", True)

TIME_COLUMN_NAME = "time"

K = TypeVar("K")
V = TypeVar("V", bound="TimeSeries")


@dataclass
class TimeSeries:
    data: DataFrame

    def __init__(self, data: DataFrame, end: datetime | None = None):
        data = self.preprocess_data(data.copy(), end)
        self.data = data

    def __add__(self, other):
        raise NotImplementedError(f"__add__ is not implemented for {type(self)}")

    def __eq__(self, other: object):
        if not isinstance(other, type(self)):
            return False
        try:
            compare_dfs(self.data, other.data)
            return True
        except AssertionError:
            return False

    def __len__(self):
        return len(self.data)

    def __getitem__(self, where: Union[slice, datetime, list[datetime]]) -> Self:
        if isinstance(where, slice):
            start, stop, step = where.start, where.stop, where.step
            if step is not None:
                logger.warning("Step is not supported for slicing. Ignoring it.")
            if not (isinstance(start, datetime) and isinstance(stop, datetime)):
                raise ValueError("Only datetime slicing is supported")
            return self.interval(start, stop)
        elif isinstance(where, datetime):
            filtered, dt = self._get_data_by_datetime(where)
            data = pd.DataFrame(filtered).T
            return self.__class__(self.preprocess_data(data, dt))
        elif isinstance(where, list):
            filtered = [self._get_data_by_datetime(time)[0] for time in where]
            data = pd.DataFrame(pd.concat(filtered, axis=1)).T
            max_dt = sorted(data.index)[-1]
            return self.__class__(self.preprocess_data(data, max_dt))
        else:
            raise ValueError("Expected datetime slice, or datetime object(s).")

    def _get_data_by_datetime(self, dt: datetime) -> Tuple[Series, datetime]:
        if dt > self.data.index[-1]:
            logger.warning(
                "Trying to access data after last time step. Returning last time step."
            )
            return self.data.iloc[-1], self.data.index[-1]  # type: ignore
        if dt < self.data.index[0]:
            logger.warning(
                "Trying to access data before first time step. Returning first time step."
            )
            return self.data.iloc[0], self.data.index[0]  # type: ignore
        else:
            return self.data.asof(dt), dt  # type: ignore

    def compare(self, other) -> None:
        if not isinstance(other, type(self)):
            raise ComparisonError(
                f"Type of self: {type(self)} != type of other: {type(other)}",
                differences=[],
            )
        try:
            compare_dfs(self.data, other.data)
        except AssertionError as e:
            raise ComparisonError(
                "Time Series are not equal.",
                differences=[(type(self), str(e))],
            )

    def copy(
        self,
        deep: bool = True,
    ) -> Self:
        if deep:
            return copy.deepcopy(self)
        return copy.copy(self)

    @staticmethod
    def attributes():
        """
        Returns a list of all attributes of the corresponding time series. The
        attributes correspond to its data columns.
        """
        return []

    @classmethod
    def empty_data(cls, attributes=None, index=None):
        """
        Returns an empty DataFrame with the attributes as columns.
        """
        if attributes is None:
            attributes = cls.attributes()
        return (
            pd.DataFrame(columns=attributes, index=index)
            if index
            else pd.DataFrame(columns=attributes)
        )

    @classmethod
    def empty(cls):
        """
        Creates an empty TimeSeries object.
        """
        return cls(cls.empty_data(cls.attributes()))

    @classmethod
    def preprocess_data(
        cls: Type[Self],
        data: DataFrame,
        end: datetime | None = None,
    ) -> DataFrame:
        """
        Preprocesses TimeSeries data.
        The end time is used to fill the last time step of the data with the end time.
        This is because we have a time discrete simulation, which means the last entry in the data
        is the state of the entity at the end of the simulation.
        Args:
            data: The data of the ResultEntities object.
            end: The end time of the time series.
            name: The name or id of the corresponding input object. Can be none.
        """
        if data.empty:
            return cls.empty_data()

        if end is not None and end.tzinfo is not None:
            end = end.replace(tzinfo=None)

        if TIME_COLUMN_NAME in data.columns:
            if not pd.api.types.is_datetime64_any_dtype(data[TIME_COLUMN_NAME]):
                try:
                    data[TIME_COLUMN_NAME] = data[TIME_COLUMN_NAME].apply(
                        lambda date_string: to_date_time(date_string)
                    )
                except ValueError | ParserError as e:
                    raise ValueError(
                        f"Could not convert {TIME_COLUMN_NAME} column to datetime64: {data[TIME_COLUMN_NAME]}"
                    ) from e
            data = data.set_index(TIME_COLUMN_NAME, drop=True)

        else:
            if not pd.api.types.is_datetime64_any_dtype(data.index):
                try:
                    data.index = data.index.map(
                        lambda date_string: to_date_time(date_string)
                    )
                except ValueError | ParserError as e:
                    raise ValueError("Could not convert index to datetime64") from e

        if end is None:
            end = max(data.index)

        last_state = data.iloc[len(data) - 1]
        if last_state.name != end:
            last_state.name = end
            data = pd.concat([data, DataFrame(last_state).transpose()])
        # todo: deal with duplicate indexes -> take later one
        data = data[~data.index.duplicated(keep="last")]
        data.sort_index(inplace=True)
        data.index.name = TIME_COLUMN_NAME
        return data

    def interval(self, start: datetime, end: datetime) -> Self:
        """
        Filters the TimeSeries for the given time interval. The data can also be filtered via object[datetime:datetime].
        See __getitem__ for more information.
        Args:
            start: The start time of the time interval.
            end: The end time of the time interval.
        Returns:
            A new TimeSeries object with the filtered data.
        """
        filtered_data = filter_data_for_time_interval(self.data, start, end)
        return self.__class__(filtered_data, end)


@dataclass(frozen=True)
class EntityKey:
    uuid: str
    name: str | None = None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EntityKey):
            return self.uuid == other.uuid
        if isinstance(other, str):
            return self.uuid == other
        return False

    def __hash__(self) -> int:
        return hash(self.uuid)

    @property
    def id(self) -> str:
        return self.name if self.name else self.uuid


class TimeSeriesDict(UserDict[K, V]):
    def __init__(self, data: dict[K, V]):
        for ts in data.values():
            if not isinstance(ts, TimeSeries):
                raise ValueError(f"Expected TimeSeries object, got {type(ts)}")
        super().__init__(data)

    def __getitem__(self, key: Any) -> V:
        try:
            return super().__getitem__(key)
        except KeyError as e:
            res = None
            for k in self.keys():
                if isinstance(k, EntityKey) and k.name == key:
                    if res is not None:
                        raise ValueError(
                            f"Can't retrieve {key} from entity keys as it is ambiguous"
                        )
                    res = self[k]
            if res is not None:
                return res
            raise e

    def get_with_key(self, key: K | str) -> tuple[K, V]:
        for k, v in self.items():
            if k == key:
                return k, v
        raise KeyError(f"Key {key} not found in TimeSeriesDict")

    def subset(self, keys: Iterable[K]) -> Self:
        """
        Returns an object containing only the keys. Nonexisting keys are
        ignored.

        Args:
            keys: the keys to subset the object with
        Returns:
            an object containing only the given keys
        """
        keys = set(keys)
        subset = {}
        for k, v in self.items():
            if k in keys:
                subset[k] = v
        return type(self)(subset)

    def subset_split(self, keys: Iterable[K]) -> tuple[Self, Self]:
        """Splits the object given the keys."""

        rmd_uuids = self.keys() - set(keys)
        return self.subset(keys), self.subset(rmd_uuids)

    def filter_by_date_time(self, time: datetime | list[datetime]) -> Self:
        """
        Filters the result by the given datetime or list of datetimes.

        Args:
            time: the time or list of times to filter by
        Returns:
            a new result containing only the given time or times
        """
        return type(self)(
            {uuid: result[time] for uuid, result in self.items()},
        )

    def interval(self, start: datetime, end: datetime) -> Self:
        """
        Filters the dictionary down to the given interval. End is inclusive.
        """
        return type(self)(
            {uuid: result.interval(start, end) for uuid, result in self.items()},
        )

    def compare(self, other: Self) -> None:
        """
        Compares the data of the two dicts, which means comparing the data of their
        time series. Raises a ComparisonError if the data is not equal.
        """
        if not isinstance(other, type(self)):
            raise ComparisonError(
                f"Type of self {type(self)} != type of other {type(other)}",
                differences=[],
            )

        keys_delta = set(self.keys()) ^ set(other.keys())
        if keys_delta:
            raise ComparisonError(
                "The following keys are not in both dicts:", differences=keys_delta
            )

        differences = []
        for key, entity in self.items():
            if key not in other:
                differences.append(f"Entity {key} not in other")
            else:
                try:
                    entity.compare(other[key])
                except ComparisonError as e:
                    differences.extend(e.differences)
        if differences:
            raise ComparisonError(
                f"Comparison of {type(self)} failed", differences=differences
            )

    def concat(self: Self, other: Self, deep: bool = True, keep="last") -> Self:
        """
        Concatenates the data of the two dicts, which means concatenating
        the data of their time series.

        NOTE: This only makes sense if the time series indexes are continuous. Given
        that we deal with discrete event data that means that the last state of self
        is valid until the first state of the other. Which would probably not be what
        you want in case the results are separated by a year.

        Args:
            other: The other ResultEntities object to concatenate with.
            deep: Whether to do a deep copy of the data.
            keep: How to handle duplicate indexes. "last" by default.
        """
        if not isinstance(other, type(self)):
            raise TypeError(f"Cannot concatenate {type(self)} and {type(other)}")

        if not set(self.keys()) == set(other.keys()):
            raise ValueError(
                "ResultDicts need to contain the same time series to be concatenated"
            )
        concat_ts = {}
        for key, entity in self.items():
            concat_ts[key] = entity.concat(other[key], deep=deep, keep=keep)
        return type(self)(concat_ts)

    @classmethod
    def empty(cls):
        return cls({})

    @staticmethod
    def extract_key(key: K, favor_id: bool = True) -> str:
        if isinstance(key, EntityKey):
            if favor_id and key.name:
                return key.name
            else:
                return key.uuid
        return str(key)


class TimeSeriesDictMixin(ABC):
    def attr_df(
        self, attr_name: str, ffill=True, favor_ids: bool = True, *args, **kwargs
    ) -> DataFrame:
        """
        Returns a DataFrame with the concatenated attribute time series values
        of all time series entities.

        NOTE: By default forward fills the resulting nan values that occur in case of
        different time resolutions of the pq results. This is valid if you are dealing
        with event discrete time series data. This might not be what you want otherwise

        Args:
            attr_name: The attribute name of the time series to extract from
                the time series entities.
            ffill: Forward fill the resulting nan values
            favor_ids: Applies when using EntityKey as key. If True, the name
                is used for the DataFrame column names otherwise uses the uuid.

        Returns:
            DataFrame: DataFrame with the concatenated time series.
        """
        if not self.values():
            return pd.DataFrame()

        if favor_ids and isinstance(next(iter(self.keys())), EntityKey):
            names = {key.name for key in self.keys()}  # type: ignore
            if len(names) < len(self.keys()):
                # Found duplicate or undefined ids, falling back to uuid usage.
                favor_ids = False

        series = []
        for key, entity in self.items():
            name = TimeSeriesDict.extract_key(key, favor_ids)
            if callable(getattr(entity, attr_name)):
                series.append(getattr(entity, attr_name)(*args, **kwargs).rename(name))
            else:
                series.append(getattr(entity.data, attr_name).rename(name))
        data = pd.concat(series, axis=1).sort_index()
        if ffill:
            return data.ffill()
        return data
