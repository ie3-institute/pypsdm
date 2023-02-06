import concurrent.futures
from dataclasses import dataclass
from datetime import datetime
from functools import partial

from pandas import DataFrame, Series

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.result.participant.flex_options import FlexOptionsResult
from psdm_analysis.models.result.participant.participant import (
    ParticipantsResult,
    ParticipantsWithSocResult,
)
from psdm_analysis.models.result.power import PQResult
from psdm_analysis.processing.series import join_series


@dataclass(frozen=True)
class ParticipantsResultContainer:
    ems: ParticipantsResult
    loads: ParticipantsResult
    fixed_feed_ins: ParticipantsResult
    pvs: ParticipantsResult
    wecs: ParticipantsResult
    storages: ParticipantsWithSocResult
    evcs: ParticipantsResult
    evs: ParticipantsWithSocResult
    hps: ParticipantsResult
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

    @classmethod
    def from_csv(
        cls,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime,
        from_agg_results: bool = False,
    ):

        with concurrent.futures.ProcessPoolExecutor() as executor:
            # warning: Breakpoints in the underlying method might not work when started from ipynb
            pa_from_csv_for_participant = partial(
                ParticipantsResultContainer.from_csv_for_participant,
                simulation_data_path,
                delimiter,
                simulation_end,
                from_agg_results,
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
                participant_result_map[participant_result.sp_type] = participant_result

        return ParticipantsResultContainer(
            loads=participant_result_map[SystemParticipantsEnum.LOAD],
            fixed_feed_ins=participant_result_map[SystemParticipantsEnum.FIXED_FEED_IN],
            pvs=participant_result_map[SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT],
            wecs=participant_result_map[SystemParticipantsEnum.WIND_ENERGY_CONVERTER],
            storages=participant_result_map[SystemParticipantsEnum.STORAGE],
            ems=participant_result_map[SystemParticipantsEnum.ENERGY_MANAGEMENT],
            evcs=participant_result_map[SystemParticipantsEnum.EV_CHARGING_STATION],
            evs=participant_result_map[SystemParticipantsEnum.ELECTRIC_VEHICLE],
            hps=participant_result_map[SystemParticipantsEnum.HEATP_PUMP],
            flex=FlexOptionsResult.from_csv(
                SystemParticipantsEnum.FLEX_OPTIONS,
                simulation_data_path,
                delimiter,
                simulation_end,
            ),
        )

    @staticmethod
    def from_csv_for_participant(
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime,
        from_agg_results: bool,
        participant: SystemParticipantsEnum,
    ):
        if participant.has_soc() and not from_agg_results:
            return ParticipantsWithSocResult.from_csv(
                participant,
                simulation_data_path,
                delimiter,
                simulation_end,
                from_agg_results,
            )
        else:
            return ParticipantsResult.from_csv(
                participant,
                simulation_data_path,
                delimiter,
                simulation_end,
                from_agg_results,
            )

    def to_list(
        self, include_em: bool = True, include_flex=True, include_empty=True
    ) -> [ParticipantsResult]:
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
                if participants.participants
            ]
        return all_participants

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
        elif sp_type == SystemParticipantsEnum.HEATP_PUMP:
            return self.hps
        else:
            raise ValueError(
                f"No return value for system participant of type: {sp_type}"
            )

    @property
    def p(self) -> DataFrame:
        p_series = [
            participants.p_sum().rename(participants.sp_type.value)
            for participants in self.to_list(include_flex=False)
        ]
        return join_series(p_series)

    def p_sum(self) -> Series:
        return self.p.sum(axis=1).rename("p_sum")

    @property
    def q(self) -> DataFrame:
        q_series = [
            participants.q_sum().rename(participants.sp_type.value)
            for participants in self.to_list(include_flex=False)
        ]
        return join_series(q_series)

    def q_sum(self) -> Series:
        return self.q.sum(axis=1).rename("q_sum")

    def find_participant_result(self, uuid: str):
        for participants_res in self.to_list(include_flex=False):
            if uuid in participants_res:
                return participants_res.get(uuid)
        return ParticipantsResult.create_empty("None")

    def to_dict(
        self, include_empty: bool = True
    ) -> {SystemParticipantsEnum, ParticipantsResult}:
        if include_empty:
            return {res.sp_type: res for res in self.to_list()}
        else:
            return {res.sp_type: res for res in self.to_list() if res.participants}

    def energies(self) -> {SystemParticipantsEnum, float}:
        return {
            sp_type: res.energy()
            for sp_type, res in self.to_dict(include_empty=False).items()
            if sp_type != SystemParticipantsEnum.FLEX_OPTIONS
        }

    def load_and_generation_energies(self) -> {SystemParticipantsEnum, float}:
        return {
            sp_type: res.load_and_generation()
            for sp_type, res in self.to_dict(include_empty=False).items()
        }

    def sum(self) -> PQResult:
        participant_res = []
        for participant in self.to_list(include_em=False, include_flex=False):
            participant_res.append(participant.sum())
        return PQResult.sum(participant_res)

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
