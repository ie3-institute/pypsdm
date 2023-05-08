from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, List, TypeVar, Union

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

    def __contains__(self, uuid: str):
        return uuid in self.data.index

    @classmethod
    def from_csv(cls, path: str, delimiter: str):
        return cls._from_csv(path, delimiter, cls.get_enum())

    @staticmethod
    @abstractmethod
    def get_enum() -> EntitiesEnum:
        pass

    def to_csv(self, path: str, delimiter: str = ","):
        df_to_csv(self.data, path, self.get_enum().get_csv_input_file_name(), delimiter)

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

    def __repr__(self):
        return self.data

    def get(self, uuid: str) -> Series:
        return self.data.loc[uuid]

    @staticmethod
    def attributes() -> List[str]:
        """
        Method that should hold all attributes field (transformed to snake_case and case-sensitive)
        of the corresponding PSDM entity
        :return:
        """
        return ["uuid", "id", "operates_from", "operates_until", "operator"]

    @classmethod
    def create_empty(cls):
        data = pd.DataFrame(columns=cls.attributes())
        return cls(data)

    def subset(self, uuids: Union[list[str], str]):
        if isinstance(uuids, str):
            uuids = [uuids]
        return type(self)(self.data.loc[uuids])

    @abstractmethod
    def nodes(self):
        pass

    def find_nodes(self, nodes: Nodes):
        return nodes.subset(self.nodes())


ResultType = TypeVar("ResultType", bound="ResultEntities")


@dataclass(frozen=True)
class ResultEntities(ABC):
    # todo: type is a reserved keyword -> rename
    type: EntitiesEnum
    name: str
    input_model: str
    data: DataFrame

    def __repr__(self):
        return self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, slice_val: slice):
        if not isinstance(slice_val, slice):
            raise ValueError("Only slicing is supported!")
        start, stop, step = slice_val.start, slice_val.stop, slice_val.step
        if step is not None:
            logging.warning("Step is not supported for slicing. Ignoring it.")
        if not (isinstance(start, datetime) and isinstance(stop, datetime)):
            raise ValueError("Only datetime slicing is supported")
        return self.filter_for_time_interval(start, stop)

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
    def create_empty(cls, entity_type: EntitiesEnum, name: str, input_model: str):
        data = cls.empty_data()
        return cls(entity_type, name, input_model, data)

    @classmethod
    def build(
        cls,
        entity_type: EntitiesEnum,
        input_model: str,
        data: DataFrame,
        end: datetime,
        name: str = "",
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
        return cls(entity_type, name, input_model, data)

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
