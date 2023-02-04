import os.path
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

import pandas as pd
from pandas import DataFrame

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.result.flex_option import FlexOptionResult
from psdm_analysis.models.result.participant.dict import ResultDict


@dataclass(frozen=True)
class FlexOptionsResult(ResultDict):
    participants: Dict[str, FlexOptionResult]

    @classmethod
    def from_csv(
        cls,
        sp_type: SystemParticipantsEnum,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime,
        from_df: bool = False,
    ) -> "FlexOptionsResult":

        if from_df:
            path = os.path.join(simulation_data_path, "flex_df.csv")
            if not os.path.exists(path):
                return cls.create_empty(SystemParticipantsEnum.FLEX_OPTIONS)
            data = pd.read_csv(
                os.path.join(simulation_data_path, "flex_df.csv"),
                delimiter=delimiter,
                index_col=0,
                header=[0, 1],
            )
            data_dicts = {}
            for uuid in data.columns.get_level_values(0):
                data_dicts[uuid] = data[uuid]
            return cls(SystemParticipantsEnum.FLEX_OPTIONS, data_dicts)

        participant_grpd_df = ResultDict.get_grpd_df(
            sp_type,
            simulation_data_path,
            delimiter,
        )

        if not participant_grpd_df:
            return cls.create_empty(SystemParticipantsEnum.FLEX_OPTIONS)

        participants = dict(
            participant_grpd_df.apply(
                lambda grp: FlexOptionResult.build(
                    sp_type,
                    grp.name,
                    grp.drop(columns=["input_model"]),
                    simulation_end,
                )
            )
        )
        return cls(sp_type, participants)

    def to_csv(self, output_path: str):
        self.to_df().to_csv(
            os.path.join(output_path, "flex_df.csv"), index_label="time"
        )

    def to_df(self) -> DataFrame:
        return pd.concat(
            [f.data for f in self.participants.values()],
            keys=self.participants.keys(),
            axis=1,
        ).ffill()

    def to_multi_index_df(
        self, participants_res  # ParticipantsResultContainer
    ) -> DataFrame:
        flex_midfs = {}
        for res in participants_res.to_list():
            uuids = res.participants.keys()
            flex_res = self.subset(uuids)
            if flex_res:
                flex_dfs = []
                participant_uuids = []
                [
                    (participant_uuids.append(uuid), flex_dfs.append(flex.data))
                    for uuid, flex in flex_res.participants.items()
                ]
                flex_midf = pd.concat(flex_dfs, keys=participant_uuids, axis=1)
                flex_midfs[res.sp_type.value] = flex_midf
        return pd.concat(flex_midfs.values(), keys=(flex_midfs.keys()), axis=1).ffill()

    def sum(self) -> FlexOptionResult:
        return FlexOptionResult.sum(list(self.participants.values()))
