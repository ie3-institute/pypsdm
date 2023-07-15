import concurrent.futures
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from typing import Optional, Union

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.io.utils import check_filter
from psdm_analysis.models.enums import SystemParticipantsEnum
from psdm_analysis.models.input.container.grid import GridContainer
from psdm_analysis.models.input.container.mixins import ContainerMixin
from psdm_analysis.models.result.participant.flex_options import FlexOptionsResult
from psdm_analysis.models.result.participant.participant import (
    ParticipantsWithSocResult,
    PQResultDict,
)
from psdm_analysis.models.result.power import PQResult


@dataclass(frozen=True)
class ParticipantsResultContainer(ContainerMixin):
    ems: PQResultDict
    loads: PQResultDict
    fixed_feed_ins: PQResultDict
    pvs: PQResultDict
    wecs: PQResultDict
    storages: ParticipantsWithSocResult
    evcs: PQResultDict
    evs: ParticipantsWithSocResult
    hps: PQResultDict
    flex: FlexOptionsResult

    def __len__(self):
        participants = self.to_list(include_empty=False)
        return sum([len(participant) for participant in participants])

    def __getitem__(self, slice_val: slice):
        if not isinstance(slice_val, slice):
            raise ValueError("Only slicing is supported!")
        start, stop, _ = slice_val.start, slice_val.stop, slice_val.step
        if not (isinstance(start, datetime) and isinstance(stop, datetime)):
            raise ValueError("Only datetime slicing is supported")
        return self.filter_for_time_interval(start, stop)

    @property
    def p(self) -> DataFrame:
        p_series = {
            participants.entity_type.value: participants.p_sum()
            for participants in self.to_list(include_flex=False)
        }
        return pd.DataFrame(p_series).sort_index().ffill().fillna(0)

    @property
    def q(self) -> DataFrame:
        q_series = {
            participants.entity_type.value: participants.q_sum()
            for participants in self.to_list(include_flex=False)
        }
        return pd.DataFrame(q_series).sort_index().ffill().fillna(0)

    def p_sum(self) -> Series:
        return self.p.sum(axis=1).rename("p_sum")

    def q_sum(self) -> Series:
        return self.q.sum(axis=1).rename("q_sum")

    def subset(self, uuids):
        return ParticipantsResultContainer(
            self.ems.subset(uuids),
            self.loads.subset(uuids),
            self.fixed_feed_ins.subset(uuids),
            self.pvs.subset(uuids),
            self.wecs.subset(uuids),
            self.storages.subset(uuids),
            self.evcs.subset(uuids),
            self.evs.subset(uuids),
            self.hps.subset(uuids),
            self.flex.subset(uuids),
        )

    def get_participants(self, sp_type: SystemParticipantsEnum):
        if sp_type == SystemParticipantsEnum.ENERGY_MANAGEMENT:
            return self.ems
        elif sp_type == SystemParticipantsEnum.LOAD:
            return self.loads
        elif sp_type == SystemParticipantsEnum.FIXED_FEED_IN:
            return self.fixed_feed_ins
        elif sp_type == SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT:
            return self.pvs
        elif sp_type == SystemParticipantsEnum.WIND_ENERGY_CONVERTER:
            return self.wecs
        elif sp_type == SystemParticipantsEnum.STORAGE:
            return self.storages
        elif sp_type == SystemParticipantsEnum.EV_CHARGING_STATION:
            return self.evcs
        elif sp_type == SystemParticipantsEnum.HEAT_PUMP:
            return self.hps
        else:
            raise ValueError(
                f"No return value for system participant of type: {sp_type}"
            )

    def find_participant_result(self, uuid: str):
        for participants_res in self.to_list(include_flex=False):
            if uuid in participants_res:
                return participants_res.get(uuid)
        return PQResultDict.create_empty("None")

    def to_dict(
        self, include_empty: bool = True
    ) -> dict[SystemParticipantsEnum, PQResultDict]:
        if include_empty:
            return {res.entity_type: res for res in self.to_list()}
        else:
            return {res.entity_type: res for res in self.to_list() if res.entities}

    def energies(self) -> dict[SystemParticipantsEnum, float]:
        return {
            sp_type: res.energy()
            for sp_type, res in self.to_dict(include_empty=False).items()
            if sp_type != SystemParticipantsEnum.FLEX_OPTIONS
        }

    def load_and_generation_energies(self) -> dict[SystemParticipantsEnum, float]:
        return {
            sp_type: res.load_and_generation()
            for sp_type, res in self.to_dict(include_empty=False).items()
        }

    def sum(self) -> PQResult:
        participant_res = []
        for participant in self.to_list(include_em=False, include_flex=False):
            participant_res.append(participant.sum())
        return PQResult.sum(participant_res)

    def to_list(
        self, include_em: bool = True, include_flex=True, include_empty=True
    ) -> list[PQResultDict]:
        optional = []
        if include_em:
            optional.append(self.ems)
        if include_flex:
            optional.append(self.flex)
        required_participants = [
            self.loads,
            self.hps,
            self.fixed_feed_ins,
            self.wecs,
            self.storages,
            self.evcs,
            self.pvs,
        ]
        all_participants = required_participants + optional
        if not include_empty:
            all_participants = [
                participants
                for participants in all_participants
                if participants.entities
            ]
        return all_participants

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return ParticipantsResultContainer(
            self.ems.filter_by_date_time(time),
            self.loads.filter_by_date_time(time),
            self.fixed_feed_ins.filter_by_date_time(time),
            self.pvs.filter_by_date_time(time),
            self.wecs.filter_by_date_time(time),
            self.storages.filter_by_date_time(time),
            self.evcs.filter_by_date_time(time),
            self.evs.filter_by_date_time(time),
            self.hps.filter_by_date_time(time),
            self.flex.filter_by_date_time(time),
        )

    def filter_for_time_interval(self, start: datetime, end: datetime):
        return ParticipantsResultContainer(
            self.ems.filter_for_time_interval(start, end),
            self.loads.filter_for_time_interval(start, end),
            self.fixed_feed_ins.filter_for_time_interval(start, end),
            self.pvs.filter_for_time_interval(start, end),
            self.wecs.filter_for_time_interval(start, end),
            self.storages.filter_for_time_interval(start, end),
            self.evcs.filter_for_time_interval(start, end),
            self.evs.filter_for_time_interval(start, end),
            self.hps.filter_for_time_interval(start, end),
            self.flex.filter_for_time_interval(start, end),
        )

    @classmethod
    def from_csv(
        cls,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime,
        grid_container: Optional[GridContainer] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ):
        check_filter(filter_start, filter_end)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # warning: Breakpoints in the underlying method might not work when started from ipynb
            pa_from_csv_for_participant = partial(
                ParticipantsResultContainer.from_csv_for_participant,
                simulation_data_path,
                delimiter,
                simulation_end,
                grid_container,
            )
            participant_results = executor.map(
                pa_from_csv_for_participant,
                filter(
                    lambda x: x != SystemParticipantsEnum.FLEX_OPTIONS,
                    SystemParticipantsEnum.values(),
                ),
            )
            participant_result_map = {}
            for participant_result in participant_results:
                participant_result_map[
                    participant_result.entity_type
                ] = participant_result

        res = ParticipantsResultContainer(
            loads=participant_result_map[SystemParticipantsEnum.LOAD],
            fixed_feed_ins=participant_result_map[SystemParticipantsEnum.FIXED_FEED_IN],
            pvs=participant_result_map[SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT],
            wecs=participant_result_map[SystemParticipantsEnum.WIND_ENERGY_CONVERTER],
            storages=participant_result_map[SystemParticipantsEnum.STORAGE],
            ems=participant_result_map[SystemParticipantsEnum.ENERGY_MANAGEMENT],
            evcs=participant_result_map[SystemParticipantsEnum.EV_CHARGING_STATION],
            evs=participant_result_map[SystemParticipantsEnum.ELECTRIC_VEHICLE],
            hps=participant_result_map[SystemParticipantsEnum.HEAT_PUMP],
            flex=FlexOptionsResult.from_csv(
                SystemParticipantsEnum.FLEX_OPTIONS,
                simulation_data_path,
                delimiter,
                simulation_end,
            ),
        )
        return (
            res
            if not filter_start
            else res.filter_for_time_interval(filter_start, filter_end)
        )

    @staticmethod
    def from_csv_for_participant(
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime,
        grid_container: Optional[GridContainer],
        participant: SystemParticipantsEnum,
    ):
        if grid_container:
            input_entities = grid_container.participants.get_participants(participant)
        else:
            input_entities = None
        if participant.has_soc():
            return ParticipantsWithSocResult.from_csv(
                participant,
                simulation_data_path,
                delimiter,
                simulation_end,
                input_entities,
            )
        else:
            return PQResultDict.from_csv(
                participant,
                simulation_data_path,
                delimiter,
                simulation_end,
                input_entities=input_entities,
            )

    @classmethod
    def create_empty(cls):
        return ParticipantsResultContainer(
            loads=PQResultDict.create_empty(SystemParticipantsEnum.LOAD),
            fixed_feed_ins=PQResultDict.create_empty(
                SystemParticipantsEnum.FIXED_FEED_IN
            ),
            pvs=PQResultDict.create_empty(
                SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT
            ),
            wecs=PQResultDict.create_empty(
                SystemParticipantsEnum.WIND_ENERGY_CONVERTER
            ),
            storages=PQResultDict.create_empty(SystemParticipantsEnum.STORAGE),
            ems=PQResultDict.create_empty(SystemParticipantsEnum.ENERGY_MANAGEMENT),
            evcs=PQResultDict.create_empty(SystemParticipantsEnum.ELECTRIC_VEHICLE),
            evs=PQResultDict.create_empty(SystemParticipantsEnum.ELECTRIC_VEHICLE),
            hps=PQResultDict.create_empty(SystemParticipantsEnum.HEAT_PUMP),
            flex=PQResultDict.create_empty(SystemParticipantsEnum.FLEX_OPTIONS),
        )
