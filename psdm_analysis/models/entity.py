import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.io import utils
from psdm_analysis.io.utils import read_csv, to_date_time
from psdm_analysis.models.input.enums import EntitiesEnum, SystemParticipantsEnum
from psdm_analysis.models.input.participant.charging import parse_evcs_type_info
from psdm_analysis.processing.dataframe import filter_data_for_time_interval


@dataclass(frozen=True)
class Entities(ABC):
    data: DataFrame

    def __len__(self):
        return len(self.data)

    def __contains__(self, uuid: str):
        return uuid in self.data.index

    @classmethod
    @abstractmethod
    def from_csv(cls, path: str, delimiter: str):
        pass

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
            data = (
                data.merge(
                    type_data, left_on="type", right_on="uuid", suffixes=("", "_type")
                )
                .drop(columns=("uuid_type"))
                .rename(columns={"id_type": "type_id"})
            )
        if entity == SystemParticipantsEnum.ENERGY_MANAGEMENT:
            data["connected_assets"] = data["connected_assets"].apply(
                lambda x: x.split(" ")
            )
        if entity == SystemParticipantsEnum.EV_CHARGING_STATION:
            type_data = data["type"].apply(
                lambda type_str: parse_evcs_type_info(type_str)
            )
            data = pd.concat([data, type_data])
        return data.set_index("uuid")

    def uuids(self):
        return self.data.index

    def ids(self):
        return self.data["id"]

    def __repr__(self):
        return self.data

    def get(self, uuid: str) -> Series:
        return self.data.loc[uuid]

    @staticmethod
    def attributes() -> List[str]:
        """
        Method that should hold all attributes field (transformed to snake_case and case sensitive)
        of the corresponding PSDM entity
        :return:
        """
        return ["uuid", "id", "operator", "operation_time"]

    @classmethod
    def create_empty(cls):
        data = pd.DataFrame(columns=cls.attributes())
        return cls(data)


@dataclass(frozen=True)
class ResultEntities(ABC):
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
        start, stop, _ = slice_val.start, slice_val.stop, slice_val.step
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
    def create_empty(cls, sp_type: SystemParticipantsEnum, name: str, input_model: str):
        data = cls.empty_data()
        return cls(sp_type, name, input_model, data)

    @classmethod
    def build(
        cls,
        sp_type: SystemParticipantsEnum,
        input_model: str,
        data: DataFrame,
        end: datetime,
        name: str = "",
    ) -> "ResultEntities":
        if data.empty:
            return cls.create_empty(sp_type, name, input_model)

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
        return cls(sp_type, name, input_model, data)

    def filter_for_time_interval(self, start: datetime, end: datetime):
        filtered_data = filter_data_for_time_interval(self.data, start, end)
        return self.build(self.type, self.input_model, filtered_data, end, self.name)

    @classmethod
    # todo: find a way for parallel calculation
    def sum(cls, results: List["ResultEntities"]) -> "ResultEntities":
        if len(results) == 0:
            return ResultEntities.create_empty(
                SystemParticipantsEnum.PARTICIPANTS_SUM, "", ""
            )
        if len(results) == 1:
            return results[0]
        agg = results[0]
        for result in results[1::]:
            agg += result
        return agg
