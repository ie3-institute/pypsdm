import logging
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Type, TypeVar, Union

from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from psdm_analysis.errors import ComparisonError
from psdm_analysis.io.utils import (
    check_filter,
    csv_to_grpd_df,
    get_file_path,
    to_date_time,
)
from psdm_analysis.models.enums import EntitiesEnum, EntityEnumType
from psdm_analysis.models.input.entity import Entities
from psdm_analysis.models.result.entity import ResultEntities

ResultDictType = TypeVar("ResultDictType", bound="ResultDict")


@dataclass(frozen=True)
class ResultDict(ABC):
    entity_type: EntitiesEnum
    entities: Dict[str, ResultEntities]

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

    def __getitem__(self, get):
        match get:
            case str():
                return self.entities[get]
            case slice():
                start, stop, step = get.start, get.stop, get.step
                if step is not None:
                    logging.warning("Step is not supported for slicing. Ignoring it.")
                if not (isinstance(start, datetime) and isinstance(stop, datetime)):
                    raise ValueError("Only datetime slicing is supported")
                entities = {
                    key: e.filter_for_time_interval(start, stop)
                    for key, e in self.entities.items()
                }
                return type(self)(self.entity_type, entities)
            case _:
                raise ValueError(
                    "Only get by uuid or datetime slice for filtering is supported."
                )

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
                f"Type of self {type(self)} != type of other {type(other)}", errors=[]
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
                f"Comparison of {type(self)} failed", errors=differences
            )

    @classmethod
    def from_csv(
        cls: Type[ResultDictType],
        entity_type: EntityEnumType,
        simulation_data_path: str,
        delimiter: str,
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
            logging.debug("There are no " + str(cls))
            return cls.create_empty(entity_type)
        if simulation_end is None:
            simulation_end = to_date_time(grpd_df["time"].max().max())
        entities = dict(
            grpd_df.apply(
                lambda grp: ResultDict.build_for_entity(
                    entity_type,
                    grp.name,
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
    def create_empty(
        cls: ResultDictType, entity_type: EntityEnumType
    ) -> ResultDictType:
        return cls(entity_type, dict())

    @staticmethod
    def build_for_entity(
        entity_type: EntityEnumType,
        input_model: str,
        data: DataFrame,
        simulation_end: datetime,
        input_entities=Optional[Entities],
    ) -> ResultDictType:
        name = None
        if input_entities is not None:
            if input_model not in input_entities.id.index:
                logging.debug(
                    f"Input model {input_model} of type {entity_type} not found in input entities. It seems like the wrong input_entities have been passed. Not assigning a name to the result."
                )
            else:
                name = input_entities.id.loc[input_model]

        return entity_type.get_result_type().build(
            entity_type, input_model, data, simulation_end, name=name
        )

    @staticmethod
    def get_grpd_df(
        entity_type: EntityEnumType,
        simulation_data_path: str,
        delimiter: str,
    ) -> Optional[DataFrameGroupBy]:
        file_name = entity_type.get_csv_result_file_name()
        path = get_file_path(simulation_data_path, file_name)

        if not path.exists():
            logging.info(
                "No results built for {} since {} does not exist".format(
                    file_name, str(path)
                )
            )
            return None

        return csv_to_grpd_df(file_name, simulation_data_path, delimiter)

    @staticmethod
    def safe_get_path(entity_type: EntityEnumType, data_path: str) -> Optional[str]:
        file_name = entity_type.get_csv_result_file_name()
        path = get_file_path(data_path, file_name)
        if path.exists():
            return path
        else:
            logging.info(
                "No results built for {} since {} does not exist".format(
                    file_name, str(path)
                )
            )
            return None
