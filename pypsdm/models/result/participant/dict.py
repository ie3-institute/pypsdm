from __future__ import annotations

import os
import uuid
from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Self, Tuple, Type

import pandas as pd
from loguru import logger

from pypsdm.io.utils import check_filter, csv_to_grpd_df, get_file_path, to_date_time
from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.input.entity import Entities
from pypsdm.models.ts.base import EntityKey, TimeSeries
from pypsdm.models.ts.types import (
    ComplexPower,
    ComplexPowerDict,
    ComplexPowerWithSoc,
    ComplexPowerWithSocDict,
)

if TYPE_CHECKING:
    from pypsdm.models.input.container.grid import GridContainer


class EntitiesResultDictMixin:

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntitiesEnum:
        raise NotImplementedError

    @classmethod
    def result_type(cls) -> Type[TimeSeries]:
        return cls.entity_type().get_result_type()

    @classmethod
    def from_csv(
        cls,
        simulation_data_path: str,
        delimiter: str | None = None,
        simulation_end: datetime | None = None,
        input_entities: Entities | None = None,
        filter_start: datetime | None = None,
        filter_end: datetime | None = None,
        must_exist: bool = True,
    ) -> Self:
        check_filter(filter_start, filter_end)

        file_name = cls.entity_type().get_csv_result_file_name()
        path = get_file_path(simulation_data_path, file_name)
        if path.exists():
            grpd_df = csv_to_grpd_df(file_name, simulation_data_path, delimiter)
        else:
            if must_exist:
                raise FileNotFoundError(f"File {path} does not exist")
            else:
                return cls.empty()  # type: ignore

        if len(grpd_df) == 0:
            return cls.empty()  # type: ignore

        if simulation_end is None:
            simulation_end = to_date_time(grpd_df["time"].max().max())  # type: ignore

        ts_dict = {}
        for key, grp in grpd_df:
            name = None
            if input_entities:
                if key in input_entities:  # type: ignore
                    name = input_entities[key].name  # type: ignore
                else:
                    logger.warning("Entity {} not in input entities".format(key))
            entity_key = EntityKey(key, name)  # type: ignore
            grp.drop(columns=["input_model"], inplace=True)
            ts = cls.result_type()(grp, simulation_end)
            ts_dict[entity_key] = ts

        res = cls(ts_dict)
        return (
            res
            if not filter_start
            else res.filter_for_time_interval(filter_start, filter_end)  # type: ignore
        )

    def to_csv(
        self,
        path: str,
        delimiter=",",
        mkdirs=False,
        resample_rate: str | None = None,
    ):
        if mkdirs:
            os.makedirs(path, exist_ok=True)

        file_name = self.entity_type().get_csv_result_file_name()

        def prepare_data(data: pd.DataFrame, input_model: str):
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
            prepare_data(participant.data, entity_key.uuid)
            for entity_key, participant in self.items()  # type: ignore
        ]
        df = pd.concat(dfs)
        df.to_csv(os.path.join(path, file_name), sep=delimiter, index=True)

    @staticmethod
    def from_csv_for_entity(
        simulation_data_path: str,
        simulation_end: datetime | None,
        grid_container: GridContainer | None,
        entity: EntitiesEnum,
        delimiter: str | None = None,
    ) -> "EntitiesResultDictMixin" | Tuple[Exception, EntitiesEnum]:
        try:
            if grid_container:
                input_entities = grid_container.participants.get_participants(entity)
            else:
                input_entities = None
            dict_type = entity.get_result_dict_type()
            return dict_type.from_csv(
                simulation_data_path,
                delimiter=delimiter,
                simulation_end=simulation_end,
                input_entities=input_entities,
                must_exist=False,
            )

        except Exception as e:
            return (e, entity)


class EmsResult(ComplexPowerDict[EntityKey], EntitiesResultDictMixin):

    def __init__(self, data: dict[EntityKey, ComplexPower]):
        for key, value in data.items():
            if not isinstance(key, EntityKey):
                raise ValueError(f"Key {key} is not of type EntityKey")
            if not isinstance(value, ComplexPower):
                raise ValueError(f"Time series {value} is not of type ComplexPower")
        super().__init__(data)

    def __getitem__(self, key: str | EntityKey) -> ComplexPower:
        if isinstance(key, str):
            key = EntityKey(key)
        else:
            key = key
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.ENERGY_MANAGEMENT


class LoadsResult(ComplexPowerDict[EntityKey], EntitiesResultDictMixin):

    def __init__(self, data: dict[EntityKey, ComplexPower]):
        for key, value in data.items():
            if not isinstance(key, EntityKey):
                raise ValueError(f"Key {key} is not of type EntityKey")
            if not isinstance(value, ComplexPower):
                raise ValueError(f"Time series {value} is not of type ComplexPower")
        super().__init__(data)

    def __getitem__(self, key: str | EntityKey) -> ComplexPower:
        if isinstance(key, str):
            key = EntityKey(key)
        else:
            key = key
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.LOAD


class FixedFeedInsResult(ComplexPowerDict[EntityKey], EntitiesResultDictMixin):

    def __init__(self, data: dict[EntityKey, ComplexPower]):
        for key, value in data.items():
            if not isinstance(key, EntityKey):
                raise ValueError(f"Key {key} is not of type EntityKey")
            if not isinstance(value, ComplexPower):
                raise ValueError(f"Time series {value} is not of type ComplexPower")
        super().__init__(data)

    def __getitem__(self, key: str | EntityKey) -> ComplexPower:
        if isinstance(key, str):
            key = EntityKey(key)
        else:
            key = key
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.FIXED_FEED_IN


class PvsResult(ComplexPowerDict[EntityKey], EntitiesResultDictMixin):

    def __init__(self, data: dict[EntityKey, ComplexPower]):
        for key, value in data.items():
            if not isinstance(key, EntityKey):
                raise ValueError(f"Key {key} is not of type EntityKey")
            if not isinstance(value, ComplexPower):
                raise ValueError(f"Time series {value} is not of type ComplexPower")
        super().__init__(data)

    def __getitem__(self, key: str | EntityKey) -> ComplexPower:
        if isinstance(key, str):
            key = EntityKey(key)
        else:
            key = key
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT


class WecsResult(ComplexPowerDict[EntityKey], EntitiesResultDictMixin):

    def __init__(self, data: dict[EntityKey, ComplexPower]):
        for key, value in data.items():
            if not isinstance(key, EntityKey):
                raise ValueError(f"Key {key} is not of type EntityKey")
            if not isinstance(value, ComplexPower):
                raise ValueError(f"Time series {value} is not of type ComplexPower")
        super().__init__(data)

    def __getitem__(self, key: str | EntityKey) -> ComplexPower:
        if isinstance(key, str):
            key = EntityKey(key)
        else:
            key = key
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.WIND_ENERGY_CONVERTER


class StoragesResult(ComplexPowerWithSocDict[EntityKey], EntitiesResultDictMixin):

    def __init__(self, data: dict[EntityKey, ComplexPowerWithSoc]):
        for key, value in data.items():
            if not isinstance(key, EntityKey):
                raise ValueError(f"Key {key} is not of type EntityKey")
            if not isinstance(value, ComplexPowerWithSoc):
                raise ValueError(
                    f"Time series {value} is not of type ComplexPowerWithSoc"
                )
        super().__init__(data)

    def __getitem__(self, key: str | EntityKey) -> ComplexPowerWithSoc:
        if isinstance(key, str):
            key = EntityKey(key)
        else:
            key = key
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.STORAGE


class EvcsResult(ComplexPowerDict[EntityKey], EntitiesResultDictMixin):
    def __getitem__(self, key: str | EntityKey) -> ComplexPower:
        if isinstance(key, str):
            key = EntityKey(key)
        else:
            key = key
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.EV_CHARGING_STATION


class EvsResult(ComplexPowerWithSocDict[EntityKey], EntitiesResultDictMixin):
    def __getitem__(self, key: str | EntityKey) -> ComplexPowerWithSoc:
        if isinstance(key, str):
            key = EntityKey(key)
        else:
            key = key
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.ELECTRIC_VEHICLE


class HpsResult(ComplexPowerDict[EntityKey], EntitiesResultDictMixin):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.HEAT_PUMP


class FlexResult(ComplexPowerDict[EntityKey], EntitiesResultDictMixin):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return SystemParticipantsEnum.FLEX_OPTIONS
