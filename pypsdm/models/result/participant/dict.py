import os
import uuid
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Generic, Optional, Self, Type, TypeVar, Union

from loguru import logger
from pandas import DataFrame
from pandas.core.groupby.generic import DataFrameGroupBy

from pypsdm.errors import ComparisonError
from pypsdm.io.utils import check_filter, csv_to_grpd_df, get_file_path, to_date_time
from pypsdm.models.enums import EntitiesEnum
from pypsdm.models.input.entity import Entities
from pypsdm.models.result.entity import ResultEntities
from pypsdm.processing.dataframe import join_dataframes

ResultDictType = TypeVar("ResultDictType", bound="ResultDict")
T = TypeVar("T", bound=ResultEntities)


@dataclass(frozen=True)
class ResultDict(Generic[T], ABC):
    entity_type: EntitiesEnum
    entities: Dict[str, T]

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.entity_type != other.entity_type:
            return False
        for key, res in self.entities.items():
            if key not in other.entities:
                return False
            if res != other.entities[key]:
                return False
        return True

    def __len__(self):
        return len(self.entities)

    def __contains__(self, uuid):
        return uuid in self.entities

    def __getitem__(self, get) -> T:
        match get:
            case str():
                return self.entities[get]
            case slice():
                raise ValueError(
                    "If you want to filter by time interval use filter_for_time_interval method instead."
                )
            case _:
                raise ValueError("Only get by uuid is supported.")

    def __add__(self: ResultDictType, other: ResultDictType):
        """
        Add two ResultDicts together. The entity types must be the same.

        BEWARE: The underlying data will NOT be copied. That means changing items in the returned ResultDict will also
        change the items in the original ResultDicts and vice versa.

        Args:
            other: The ResultDict to add to this ResultDict

        Returns:
            A new ResultDict containing the entities of both ResultDicts.
        """
        if not isinstance(other, type(self)):
            raise TypeError(f"Cannot add {type(self)} and {type(other)}")
        if self.entity_type != other.entity_type:
            raise TypeError(
                f"Cannot add {type(self)} and {type(other)}. Entities are of different entity types"
            )
        return type(self)(self.entity_type, {**self.entities, **other.entities})

    def __sub__(self: ResultDictType, other: ResultDictType):
        """
        Creates a new dict with the elements of self minus all keys of other. The entity types must be the same.

        BEWARE: Returns a shallow copy of the data, the underlying data will NOT be copied.

        Args:
            other: The ResultDict to subtract from this ResultDict

        """
        if not isinstance(other, type(self)):
            raise TypeError(f"Cannot subtract {type(self)} and {type(other)}")
        if self.entity_type != other.entity_type:
            raise TypeError(
                f"Cannot subtract {type(self)} and {type(other)}. Entities are of different entity types"
            )
        keys = self.entities.keys() - other.entities.keys()
        return type(self)(self.entity_type, {key: self.entities[key] for key in keys})

    def __iter__(self):
        return self.entities.__iter__()

    def keys(self):
        return self.entities.keys()

    def values(self):
        return self.entities.values()

    def to_list(self):
        return list(self.entities.values())

    def items(self):
        return self.entities.items()

    def uuids(self):
        return list(self.entities.keys())

    def results(self):
        return list(self.entities.values())

    # noinspection PyArgumentList
    def subset(self, uuids):
        matched_participants = {
            uuid: self.entities[uuid] for uuid in self.entities.keys() & uuids
        }

        return type(self)(self.entity_type, matched_participants)

    def subset_split(self, uuids: list[str]):
        """
        Returns a results result containing the given uuids and a results result containing the remaining uuids.
        :param uuids: the uuids with which to split the result
        :return:
        """

        rmd_uuids = self.entities.keys() - uuids
        return self.subset(uuids), self.subset(rmd_uuids)

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        """
        Filters the result by the given datetime or list of datetimes.
        :param time: the time or list of times to filter by
        :return: a new result containing only the given time or times
        """
        return type(self)(
            self.entity_type,
            {uuid: result[time] for uuid, result in self.entities.items()},
        )

    # noinspection PyArgumentList
    def filter_for_time_interval(self, start: datetime, end: datetime):
        return type(self)(
            self.entity_type,
            {
                uuid: result.filter_for_time_interval(start, end)
                for uuid, result in self.entities.items()
            },
        )

    def uuid_to_id_map(self) -> dict[str, Optional[str]]:
        return {uuid: result.name for uuid, result in self.entities.items()}

    def compare(self, other):
        if not isinstance(other, type(self)):
            raise ComparisonError(
                f"Type of self {type(self)} != type of other {type(other)}",
                differences=[],
            )
        differences = []
        if self.entity_type != other.entity_type:
            differences.append(f"Entity type {self.entity_type} != {other.entity_type}")
        for key, entity in self.entities.items():
            if key not in other.entities:
                differences.append(f"Entity {key} not in other")
            else:
                try:
                    entity.compare(other.entities[key])
                except ComparisonError as e:
                    differences.extend(e.differences)
        if differences:
            raise ComparisonError(
                f"Comparison of {type(self)} failed", differences=differences
            )

    def concat(
        self: ResultDictType, other: ResultDictType, deep: bool = True, keep="last"
    ):
        """
        Concatenates the data of the two ResultDicts, which means concatenating
        the data of their entities.

        NOTE: This only makes sense if the entities indexes are continuous. Given
        that we deal with discrete event data that means that the last state of self
        is valid until the first state of other. Which would probably not be what
        you want in case the results are separated by a year.

        Args:
            other: The other ResultEntities object to concatenate with.
            deep: Whether to do a deep copy of the data.
            keep: How to handle duplicate indexes. "last" by default.
        """
        if not isinstance(other, type(self)):
            raise TypeError(f"Cannot concatenate {type(self)} and {type(other)}")
        if self.entity_type != other.entity_type:
            raise TypeError(
                f"Cannot add {type(self)} and {type(other)}. Entities are of different entity types"
            )

        if not set(self.entities.keys()) == set(other.entities.keys()):
            raise ValueError(
                "ResultDicts need to contain the same entities to be concatenated"
            )
        concat_entities = {}
        for key, entity in self.entities.items():
            concat_entities[key] = entity.concat(
                other.entities[key], deep=deep, keep=keep
            )
        return type(self)(self.entity_type, concat_entities)

    def to_csv(
        self,
        path: str,
        delimiter=",",
        mkdirs=False,
        resample_rate: Optional[str] = None,
    ):
        if mkdirs:
            os.makedirs(path, exist_ok=True)

        file_name = self.entity_type.get_csv_result_file_name()

        def prepare_data(data: DataFrame, input_model: str):
            data = data.copy()
            data = (
                data.resample("60s").ffill().resample(resample_rate).mean()
                if resample_rate
                else data
            )
            data["uuid"] = data.apply(lambda _: str(uuid.uuid4()), axis=1)
            data["input_model"] = input_model
            data.index.name = "time"
            return data

        dfs = [
            prepare_data(participant.data, input_model)
            for input_model, participant in self.entities.items()
        ]
        df = join_dataframes(dfs)
        df.to_csv(os.path.join(path, file_name), sep=delimiter, index=True)

    @classmethod
    def from_csv(
        cls: Type[ResultDictType],
        entity_type: EntitiesEnum,
        simulation_data_path: str,
        delimiter: str | None = None,
        simulation_end: Optional[datetime] = None,
        input_entities: Optional[Entities] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ) -> ResultDictType:
        check_filter(filter_start, filter_end)
        grpd_df = ResultDict.get_grpd_df(
            entity_type,
            simulation_data_path,
            delimiter,
        )
        if not grpd_df:
            logger.debug("There are no " + str(cls))
            return cls.create_empty(entity_type)
        if simulation_end is None:
            simulation_end = to_date_time(grpd_df["time"].max().max())
        entities = dict(
            grpd_df.apply(
                lambda grp: ResultDict.build_for_entity(
                    entity_type,
                    grp.name,  # type: ignore
                    grp.drop(columns=["input_model"]),
                    simulation_end,
                    input_entities=input_entities,
                )
            )
        )
        res = cls(
            entity_type,
            entities,
        )
        return (
            res
            if not filter_start
            else res.filter_for_time_interval(filter_start, filter_end)
        )

    @classmethod
    def create_empty(cls: Type[Self], entity_type: EntitiesEnum) -> Self:
        return cls(entity_type, dict())

    @staticmethod
    def build_for_entity(
        entity_type: EntitiesEnum,
        input_model: str,
        data: DataFrame,
        simulation_end: datetime,
        input_entities: Optional[Entities],
    ) -> ResultEntities:
        name = None
        if input_entities is not None:
            if input_model not in input_entities.id.index:
                logger.debug(
                    f"Input model {input_model} of type {entity_type} not found in input entities. It seems like the wrong input_entities have been passed. Not assigning a name to the result."
                )
            else:
                name = input_entities.id.loc[input_model]

        return entity_type.get_result_type().build(
            entity_type, input_model, data, simulation_end, name=name
        )

    @staticmethod
    def get_grpd_df(
        entity_type: EntitiesEnum,
        simulation_data_path: str,
        delimiter: str | None = None,
    ) -> Optional[DataFrameGroupBy]:
        file_name = entity_type.get_csv_result_file_name()
        path = get_file_path(simulation_data_path, file_name)

        if not path.exists():
            logger.info(
                "No results built for {} since {} does not exist".format(
                    file_name, str(path)
                )
            )
            return None

        return csv_to_grpd_df(file_name, simulation_data_path, delimiter)

    @staticmethod
    def safe_get_path(entity_type: EntitiesEnum, data_path: str) -> Optional[Path]:
        file_name = entity_type.get_csv_result_file_name()
        path = get_file_path(data_path, file_name)
        if path.exists():
            return path
        else:
            logger.info(
                "No results built for {} since {} does not exist".format(
                    file_name, str(path)
                )
            )
            return None
