from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple, TypeVar, Union

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.io import utils
from psdm_analysis.io.utils import df_to_csv, read_csv, to_date_time
from psdm_analysis.models.input.enums import (
    EntitiesEnum,
    RawGridElementsEnum,
    SystemParticipantsEnum,
)
from psdm_analysis.models.input.participant.charging import parse_evcs_type_info
from psdm_analysis.processing.dataframe import filter_data_for_time_interval

if TYPE_CHECKING:
    from psdm_analysis.models.input.node import Nodes

EntityType = TypeVar("EntityType", bound="Entities")


@dataclass(frozen=True)
class Entities(ABC):
    data: DataFrame

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return self.data

    def __contains__(self, uuid: str):
        return uuid in self.data.index

    def __add__(self: EntityType, other: EntityType) -> EntityType:
        """
        Concatenates two Entities instances.

        Args:
            other: The other Entities instance to concatenate with.

        Returns:
            The concatenated Entities instance.
        """

        if not isinstance(other, type(self)):
            raise TypeError("The two Entities instances must be of the same type")

        columns_diff = set(self.data.columns).symmetric_difference(other.data.columns)
        if len(columns_diff) > 0 and columns_diff.issubset(self.attributes()):
            logging.warning(
                "The two Entities instances have different columns: %s", columns_diff
            )
        else:
            return type(self)(pd.concat([self.data, other.data]))

    def __sub__(self: EntityType, other: Union[EntityType, List[str]]) -> EntityType:
        """
        Subtacts the entities with the given uuids from the Entities instance.

        Args:
            other: The other Entities instance or a list of uuids to subtract.

        Returns:
            A new Entities instance with the uuids removed.
        """

        if isinstance(other, Entities):
            indices_to_remove = other.data.index
        elif isinstance(other, list) and all(isinstance(index, str) for index in other):
            indices_to_remove = other
        else:
            raise TypeError("other must be an Entities instance or a list of strings")

        if not set(indices_to_remove).issubset(self.data.index):
            raise ValueError(
                f"All indices to remove must exist in the current Entities instance: {set(indices_to_remove) - set(self.data.index)}"
            )

        return type(self)(self.data.drop(indices_to_remove))

    @property
    def uuids(self):
        return self.data.index

    @property
    def ids(self):
        return self.data["id"]

    @property
    def operates_from(self):
        return self.data["operates_from"]

    @property
    def operates_until(self):
        return self.data["operates_until"]

    @property
    def operator(self):
        return self.data["operator"]

    @abstractmethod
    def nodes(self):
        pass

    def get(self, uuid: str) -> Series:
        return self.data.loc[uuid]

    def subset(self, uuids: Union[list[str], set[str], str]):
        if isinstance(uuids, str):
            uuids = [uuids]
        elif isinstance(uuids, set):
            uuids = list(uuids)
        return type(self)(self.data.loc[uuids])

    def subset_id(self, ids: Union[list[str], set[str], str]):
        if isinstance(ids, str):
            ids = [ids]
        elif isinstance(ids, set):
            ids = list(ids)
        return type(self)(self.data[self.data["id"].isin(ids)])

    def subset_split(self, uuids: list[str]):
        rmd = set(self.uuids) - set(uuids)
        return self.subset(uuids), self.subset(list(rmd))

    def filter_by_nodes(self, nodes: Union[str, list[str], set[str]]) -> EntityType:
        """
        Filters for all entities which are connected to one of th given nodes.

        Args:
            nodes: The nodes to filter by, represented by their uuids.

        Returns:
            A new Entities instance with the filtered entities.
        """
        if isinstance(nodes, str):
            nodes = [nodes]
        data = self.data[self.nodes().isin(nodes)]
        return type(self)(data)

    def find_nodes(self, nodes: Nodes) -> Nodes:
        return nodes.subset(self.nodes())

    def to_csv(self, path: str, delimiter: str = ","):
        df_to_csv(self.data, path, self.get_enum().get_csv_input_file_name(), delimiter)

    @classmethod
    def from_csv(cls, path: str, delimiter: str):
        return cls._from_csv(path, delimiter, cls.get_enum())

    @classmethod
    def _from_csv(cls, path: str, delimiter: str, entity: EntitiesEnum):
        file_path = utils.get_file_path(path, entity.get_csv_input_file_name())
        if os.path.exists(file_path):
            return cls(Entities._data_from_csv(entity, path, delimiter))
        else:
            logging.debug(
                "There is no file named: "
                + str(file_path)
                + ". No "
                + entity.value
                + " entities are loaded."
            )
            return cls.create_empty()

    @classmethod
    def _data_from_csv(
        cls, entity: EntitiesEnum, path: str, delimiter: str
    ) -> DataFrame:
        data = read_csv(path, entity.get_csv_input_file_name(), delimiter)
        if entity.has_type():
            type_data = read_csv(path, entity.get_type_file_name(), delimiter)
            data = data.merge(
                type_data, left_on="type", right_on="uuid", suffixes=("", "_type")
            ).rename(columns={"id_type": "type_id", "uuid_type": "type_uuid"})
        # special data transformations
        match entity:
            # for raw grid elements
            # ---------------------
            case RawGridElementsEnum.NODE:
                data["longitude"] = data["geo_position"].apply(
                    lambda geo_json: json.loads(geo_json)["coordinates"][0]
                )
                data["latitude"] = data["geo_position"].apply(
                    lambda geo_json: json.loads(geo_json)["coordinates"][1]
                )

            # for system participants
            # -----------------------
            case SystemParticipantsEnum.ENERGY_MANAGEMENT:
                data["connected_assets"] = data["connected_assets"].apply(
                    lambda x: x.split(" ")
                )
            case SystemParticipantsEnum.EV_CHARGING_STATION:
                type_data = data["type"].apply(
                    lambda type_str: parse_evcs_type_info(type_str)
                )
                data = pd.concat([data, type_data])

        try:
            return data.set_index("uuid")
        except KeyError as e:
            raise KeyError(
                "Column 'uuid' not found. This might be due to wrong csv delimiter!", e
            )

    @classmethod
    def create_empty(cls):
        data = pd.DataFrame(columns=cls.attributes())
        return cls(data)

    @staticmethod
    @abstractmethod
    def get_enum() -> EntitiesEnum:
        pass

    @staticmethod
    def attributes() -> List[str]:
        """
        Method that should hold all attributes field (transformed to snake_case and case-sensitive)
        of the corresponding PSDM entity
        :return:
        """
        return ["uuid", "id", "operates_from", "operates_until", "operator"]


ResultType = TypeVar("ResultType", bound="ResultEntities")


@dataclass(frozen=True)
class ResultEntities(ABC):
    # todo: type is a reserved keyword -> rename
    type: EntitiesEnum
    input_model: str
    name: Optional[str]
    data: DataFrame

    def __repr__(self):
        return self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, where: Union[slice, datetime, list[datetime]]):
        if isinstance(where, slice):
            start, stop, step = where.start, where.stop, where.step
            if step is not None:
                logging.warning("Step is not supported for slicing. Ignoring it.")
            if not (isinstance(start, datetime) and isinstance(stop, datetime)):
                raise ValueError("Only datetime slicing is supported")
            return self.filter_for_time_interval(start, stop)
        elif isinstance(where, datetime):
            filtered, dt = self._get_data_by_datetime(where)
            data = pd.DataFrame(filtered).T
            return self.build(self.type, self.input_model, data, dt, self.name)
        elif isinstance(where, list):
            filtered = [self._get_data_by_datetime(time)[0] for time in where]
            data = pd.DataFrame(pd.concat(filtered, axis=1)).T
            max_dt = sorted(data.index)[-1]
            return self.build(self.type, self.input_model, data, max_dt, name=self.name)

    def _get_data_by_datetime(self, dt: datetime) -> Tuple[Series, datetime]:
        if dt > self.data.index[-1]:
            logging.warning(
                "Trying to access data after last time step. Returning last time step."
            )
            return self.data.iloc[-1], self.data.index[-1]
        if dt < self.data.index[0]:
            logging.warning(
                "Trying to access data before first time step. Returning first time step."
            )
            return self.data.iloc[0], self.data.index[0]
        else:
            return self.data.asof(dt), dt

    @staticmethod
    @abstractmethod
    def attributes() -> List[str]:
        pass

    @classmethod
    def empty_data(cls, index=None):
        return (
            pd.DataFrame(columns=cls.attributes(), index=index)
            if index
            else pd.DataFrame(columns=cls.attributes())
        )

    @classmethod
    def create_empty(
        cls, entity_type: EntitiesEnum, name: Optional[str], input_model: str
    ):
        data = cls.empty_data()
        return cls(entity_type, input_model, name, data)

    @classmethod
    def build(
        cls,
        entity_type: EntitiesEnum,
        input_model: str,
        data: DataFrame,
        end: datetime,
        name: Optional[str] = None,
    ) -> "ResultEntities":
        if data.empty:
            return cls.create_empty(entity_type, name, input_model)

        if "time" in data.columns:
            data["time"] = data["time"].apply(
                lambda date_string: to_date_time(date_string)
            )
            data = data.set_index("time", drop=True)

        last_state = data.iloc[len(data) - 1]
        if last_state.name != end:
            last_state.name = end
            data = pd.concat([data, DataFrame(last_state).transpose()])
        # todo: deal with duplicate indexes -> take later one
        data = data[~data.index.duplicated(keep="last")]
        data.sort_index(inplace=True)
        return cls(entity_type, input_model, name, data)

    def filter_for_time_interval(self, start: datetime, end: datetime):
        filtered_data = filter_data_for_time_interval(self.data, start, end)
        return self.build(self.type, self.input_model, filtered_data, end, self.name)

    @classmethod
    # todo: find a way for parallel calculation
    def sum(cls, results: list[ResultType]) -> ResultType:
        if len(results) == 0:
            return cls.create_empty(SystemParticipantsEnum.PARTICIPANTS_SUM, "", "")
        if len(results) == 1:
            return results[0]
        agg = results[0]
        for result in results[1::]:
            agg += result
        return agg

    def find_input_entity(self, input_model: EntityType):
        if self.type != input_model.get_enum():
            logging.warning("Input model type does not match result type!")
        return input_model.subset([self.input_model])
