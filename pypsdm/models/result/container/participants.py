from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Self, Tuple, Union

import pandas as pd
from pandas import DataFrame, Series

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.input.container.grid import GridContainer
from pypsdm.models.input.container.mixins import ResultContainerMixin
from pypsdm.models.result.participant.dict import (
    EmsResult,
    EvcsResult,
    EvsResult,
    FixedFeedInsResult,
    HpsResult,
    LoadsResult,
    PvsResult,
    StoragesResult,
    WecsResult,
)
from pypsdm.models.result.participant.flex_options import FlexOptionsDict
from pypsdm.models.ts.base import EntityKey, TimeSeriesDict
from pypsdm.models.ts.types import ComplexPower, ComplexPowerDict


@dataclass
class SystemParticipantsResultContainer(ResultContainerMixin):
    ems: EmsResult
    loads: LoadsResult
    fixed_feed_ins: FixedFeedInsResult
    pvs: PvsResult
    wecs: WecsResult
    storages: StoragesResult
    evcs: EvcsResult
    evs: EvsResult
    hps: HpsResult
    flex: FlexOptionsDict

    def __init__(self, dct: dict[EntitiesEnum, TimeSeriesDict]):
        def get_or_empty(key: EntitiesEnum, dict_type):
            value = dct.get(key, dict_type.empty())
            if not isinstance(value, dict_type):
                raise ValueError(f"Expected {dict_type} but got {type(value)}")
            return value

        self.ems = get_or_empty(SystemParticipantsEnum.ENERGY_MANAGEMENT, EmsResult)  # type: ignore
        self.loads = get_or_empty(SystemParticipantsEnum.LOAD, LoadsResult)  # type: ignore
        self.fixed_feed_ins = get_or_empty(
            SystemParticipantsEnum.FIXED_FEED_IN, FixedFeedInsResult
        )  # type: ignore
        self.pvs = get_or_empty(
            SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT, PvsResult
        )  # type: ignore
        self.wecs = get_or_empty(
            SystemParticipantsEnum.WIND_ENERGY_CONVERTER, WecsResult
        )  # type: ignore
        self.storages = get_or_empty(SystemParticipantsEnum.STORAGE, StoragesResult)  # type: ignore
        self.evcs = get_or_empty(SystemParticipantsEnum.EV_CHARGING_STATION, EvcsResult)  # type: ignore
        self.evs = get_or_empty(SystemParticipantsEnum.ELECTRIC_VEHICLE, EvsResult)  # type: ignore
        self.hps = get_or_empty(SystemParticipantsEnum.HEAT_PUMP, HpsResult)  # type: ignore
        self.flex = get_or_empty(SystemParticipantsEnum.FLEX_OPTIONS, FlexOptionsDict)  # type: ignore

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def __len__(self):
        participants = self.to_list(include_empty=False)
        return sum([len(participant) for participant in participants])

    def __getitem__(self, slice_val: slice) -> "SystemParticipantsResultContainer":
        if not isinstance(slice_val, slice):
            raise ValueError("Only datetime slicing is supported!")
        start, stop, _ = slice_val.start, slice_val.stop, slice_val.step
        if not (isinstance(start, datetime) and isinstance(stop, datetime)):
            raise ValueError("Only datetime slicing is supported")
        return self.interval(start, stop)

    def __add__(self, other: "SystemParticipantsResultContainer"):
        raise NotImplementedError("Adding of ParticipantsResultContainer not supported")

    def p(self) -> DataFrame:
        p_series = {
            participants.entity_type().value: participants.p_sum()  # type: ignore
            for participants in self.participants_to_list()
        }
        return pd.DataFrame(p_series).sort_index().ffill().fillna(0)

    def q(self) -> DataFrame:
        q_series = {
            participants.entity_type().value: participants.q_sum()  # type: ignore
            for participants in self.participants_to_list()
        }
        return pd.DataFrame(q_series).sort_index().ffill().fillna(0)

    def p_sum(self) -> Series:
        return self.p().sum(axis=1).rename("p_sum")

    def q_sum(self) -> Series:
        return self.q().sum(axis=1).rename("q_sum")

    def subset(self, uuids: Iterable[str] | Iterable[EntityKey]) -> Self:
        return self.__class__({k: v.subset(uuids) for k, v in self.to_dict().items()})

    def get_participants(
        self, sp_type: SystemParticipantsEnum
    ) -> TimeSeriesDict | None:
        return self.to_dict().get(sp_type)

    def find_participant_result(self, uuid: str):
        for participants_res in self.to_list():
            if uuid in participants_res:
                return participants_res.get(uuid)
        return ValueError(f"No participant result with uuid: {uuid}")

    def energies(self) -> dict[SystemParticipantsEnum, float]:
        return {
            sp_type: res.energy()
            for sp_type, res in self.participants_to_dict(include_empty=False).items()
            if sp_type != SystemParticipantsEnum.FLEX_OPTIONS
        }

    def load_and_generation_energies(self) -> dict[EntitiesEnum, Tuple[float, float]]:
        return {
            sp_type: res.load_and_generation()
            for sp_type, res in self.participants_to_dict(include_empty=False).items()
        }

    def sum(self) -> ComplexPower:
        participant_res = []
        for participant in self.participants_to_list(include_em=False):
            participant_res.append(participant.sum())
        return ComplexPower.sum(participant_res)

    def participants_to_dict(
        self, include_empty: bool = False
    ) -> dict[SystemParticipantsEnum, ComplexPowerDict]:
        dct = {
            SystemParticipantsEnum.ENERGY_MANAGEMENT: self.ems,
            SystemParticipantsEnum.LOAD: self.loads,
            SystemParticipantsEnum.FIXED_FEED_IN: self.fixed_feed_ins,
            SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT: self.pvs,
            SystemParticipantsEnum.WIND_ENERGY_CONVERTER: self.wecs,
            SystemParticipantsEnum.STORAGE: self.storages,
            SystemParticipantsEnum.EV_CHARGING_STATION: self.evcs,
            SystemParticipantsEnum.ELECTRIC_VEHICLE: self.evs,
            SystemParticipantsEnum.HEAT_PUMP: self.hps,
        }
        if not include_empty:
            dct = {k: v for k, v in dct.items() if len(v) > 0}
        return dct

    def participants_to_list(
        self, include_em: bool = True, include_empty=True
    ) -> list[ComplexPowerDict]:  # type: ignore
        dct = self.participants_to_dict(include_empty)
        if not include_em:
            del dct[SystemParticipantsEnum.ENERGY_MANAGEMENT]
        return list(dct.values())

    def to_dict(
        self, include_empty: bool = False
    ) -> dict[SystemParticipantsEnum, TimeSeriesDict]:
        dct: dict[SystemParticipantsEnum, TimeSeriesDict] = self.participants_to_dict(
            include_empty=True
        )

        dct[SystemParticipantsEnum.FLEX_OPTIONS] = self.flex

        if not include_empty:
            dct = {k: v for k, v in dct.items() if len(v) > 0}
        return dct

    def to_list(
        self, include_em: bool = True, include_empty=True
    ) -> list[TimeSeriesDict]:  # type: ignore
        dct = self.to_dict(include_empty)
        if not include_em:
            del dct[SystemParticipantsEnum.ENERGY_MANAGEMENT]
        return list(dct.values())

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return self.__class__(
            {k: v.filter_by_date_time(time) for k, v in self.to_dict().items()}
        )

    def interval(self, start: datetime, end: datetime):
        return self.__class__(
            {k: v.interval(start, end) for k, v in self.to_dict().items()}
        )

    def concat(
        self, other: "SystemParticipantsResultContainer", deep=True, keep="last"
    ):
        """
        Concatenates the data of the current and the other ParticipantsResultContainer
        object. Concatenation is done along the index (appending rows).

        NOTE: This only makes sense if result indexes are continuous. Given that
        we deal with discrete event data that means that the last state of self
        is valid until the first state of other. Which would probably not be what
        you want in case the results are separated by a year.

        If you want to add the underlying entities, use the `__add__` method.

        Args:
            other: The other ResultDict object to concatenate with.
            deep: Whether to do a deep copy of the data.
            keep: How to handle duplicate indexes. "last" by default.
        """
        return self.__class__(
            {
                k: v.concat(other.to_dict()[k], deep=deep, keep=keep)
                for k, v in self.to_dict().items()
            }
        )

    def to_csv(self, path: str, delimiter: str = ",", mkdirs=False):
        for participant in self.to_list(include_empty=False):
            participant.to_csv(path, delimiter, mkdirs=mkdirs)

    @classmethod
    def from_csv(
        cls,
        simulation_data_path: str | Path,
        simulation_end: Optional[datetime] = None,
        grid_container: Optional[GridContainer] = None,
        delimiter: Optional[str] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ):
        dct = cls.entities_from_csv(
            simulation_data_path,
            simulation_end,
            grid_container,
            delimiter,
            filter_start,
            filter_end,
        )

        res = SystemParticipantsResultContainer(dct)  # type: ignore
        return (
            res if not filter_start else res.interval(filter_start, filter_end)  # type: ignore
        )

    @classmethod
    def entity_keys(cls) -> set[SystemParticipantsEnum]:
        return set(
            SystemParticipantsResultContainer({}).to_dict(include_empty=True).keys()
        )

    @classmethod
    def empty(cls) -> Self:
        return cls({})
