import logging
import os.path
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.participant import (
    SystemParticipantsWithCapacity,
)
from psdm_analysis.models.result.participant.dict import ResultDict
from psdm_analysis.models.result.power import PQResult, PQWithSocResult
from psdm_analysis.processing.dataframe import join_dataframes


@dataclass(frozen=True)
class ParticipantsResult(ResultDict):
    participants: Dict[str, PQResult]

    @classmethod
    def from_csv(
        cls,
        sp_type: SystemParticipantsEnum,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime,
        from_agg_res: bool = False,
    ) -> "ParticipantsResult":

        if from_agg_res:
            path = ResultDict.safe_get_path(sp_type, simulation_data_path)
            if not path:
                return cls.create_empty(sp_type)
            agg_res = pd.read_csv(path)
            agg_res["time"] = pd.to_datetime(agg_res["time"])
            agg_res = agg_res.set_index("time", drop=True)
            if "q" not in agg_res.columns:
                agg_res["q"] = 0
            agg_pq = PQResult(
                sp_type, "aggregated_result", "aggregated_result", agg_res
            )
            return ParticipantsResult(sp_type, {"aggregated": agg_pq})

        else:
            participant_grpd_df = ResultDict.get_grpd_df(
                sp_type,
                simulation_data_path,
                delimiter,
            )
            if not participant_grpd_df:
                logging.debug("There are no " + str(cls))
                return cls.create_empty(sp_type)
            participants = dict(
                participant_grpd_df.apply(
                    lambda grp: PQResult.build(
                        sp_type,
                        grp.name,
                        grp.drop(columns=["input_model"]),
                        simulation_end,
                    )
                )
            )
            return cls(
                sp_type,
                participants,
            )

    def to_csv(self, path: str, resample_rate: str = None):
        file_name = self.sp_type.get_csv_result_file_name()

        def resample(data: DataFrame, input_model: str):
            data = (
                data.resample("60s").ffill().resample(resample_rate).mean()
                if resample_rate
                else data
            )
            data["uuid"] = data.apply(lambda _: uuid.uuid4(), axis=1)
            data["input_model"] = input_model
            return data

        resampled = [
            resample(participant.data, input_model)
            for input_model, participant in self.participants.items()
        ]
        df = join_dataframes(resampled)
        df.to_csv(os.path.join(path, file_name))

    def nodal_results(self, node_uuid: str) -> "ParticipantsResult":
        pass

    def get(self, key: str) -> PQResult:
        return self.participants[key]

    def subset(self, uuids):
        return type(self)(
            self.sp_type,
            {
                uuid: self.participants[uuid]
                for uuid in self.participants.keys() & uuids
            },
        )

    @property
    def p(self):
        if not self.participants.values():
            return None
        return pd.DataFrame(
            {p_uuid: res.p for p_uuid, res in self.participants.items()}
        )

    def sum(self) -> PQResult:
        return PQResult.sum(list(self.participants.values()))

    def p_sum(self) -> Series:
        if not self.participants:
            return Series(dtype=float)
        return self.p.fillna(method="ffill").sum(axis=1).rename("p_sum")

    @property
    def q(self):
        return pd.DataFrame(
            {p_uuid: res.q for p_uuid, res in self.participants.items()}
        )

    def q_sum(self):
        if not self.participants:
            return Series(dtype=float)
        return self.q.fillna(method="ffill").sum(axis=1).rename("q_sum")

    def energy(self):
        # todo make concurrent
        sum = 0
        for participant in self.participants.values():
            sum += participant.energy()
        return sum

    def load_and_generation(self):
        return self.sum().load_and_generation()


@dataclass(frozen=True)
class ParticipantsWithSocResult(ParticipantsResult):
    sp_type: SystemParticipantsEnum
    participants: Dict[str, PQWithSocResult]

    @classmethod
    def from_csv(
        cls,
        sp_type: SystemParticipantsEnum,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime,
        from_agg_res: bool = False,
    ) -> "ParticipantsWithSocResult":

        if from_agg_res:
            raise ValueError(
                "Aggregated results do not contain SOC information. Consider reading as `ParticipantsResult`"
            )

        participant_grpd_df = ResultDict.get_grpd_df(
            sp_type,
            simulation_data_path,
            delimiter,
        )

        if not participant_grpd_df:
            logging.debug(f"There are no {sp_type.value} results.")
            return cls.create_empty(sp_type)

        participants = dict(
            participant_grpd_df.apply(
                lambda grp: PQWithSocResult.build(
                    sp_type,
                    grp.name,
                    grp.drop(columns=["input_model"]),
                    simulation_end,
                )
            )
        )
        return cls(sp_type, participants)

    def sum_with_soc(self, inputs: SystemParticipantsWithCapacity) -> PQWithSocResult:
        if not self.participants:
            return PQWithSocResult.create_empty(self.sp_type, "", "")
        capacity_participant = []
        for participant_uuid, res in self.participants.items():
            capacity = inputs.get(participant_uuid)[inputs.capacity_attribute()]
            capacity_participant.append((capacity, res))
        return PQWithSocResult.sum_with_soc(capacity_participant)
