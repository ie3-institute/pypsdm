import os.path
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import pandas as pd
from pandas import DataFrame, Series

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.result.entity import ResultEntities
from pypsdm.models.result.participant.dict import ResultDict
from pypsdm.models.result.power import PQResult
from pypsdm.processing.series import add_series, hourly_mean_resample


@dataclass(frozen=True)
class FlexOptionResult(ResultEntities):
    def __add__(self, other: "FlexOptionResult"):
        p_ref_sum = add_series(self.p_ref(), other.p_ref(), "p_ref")
        p_min_sum = add_series(self.p_min(), other.p_min(), "p_min")
        p_max_sum = add_series(self.p_max(), other.p_max(), "p_max")
        summed_data = p_ref_sum.to_frame().join([p_min_sum, p_max_sum])
        return FlexOptionResult(
            self.entity_type,
            "FlexResult - Sum",
            "FlexResult - Sum",
            summed_data,
        )

    @staticmethod
    def attributes() -> List[str]:
        return ["p_max", "p_min", "p_ref"]

    def p_max(self):
        return self.data["p_max"]

    def p_min(self):
        return self.data["p_min"]

    def p_ref(self):
        return self.data["p_ref"]

    def p_max_as_pq(self, sp_type: SystemParticipantsEnum) -> PQResult:
        return self._p_to_pq_res(sp_type, self.p_max())

    def p_ref_as_pq(self, sp_type: SystemParticipantsEnum) -> PQResult:
        return self._p_to_pq_res(sp_type, self.p_ref())

    def p_min_as_pq(self, sp_type: SystemParticipantsEnum):
        return self._p_to_pq_res(sp_type, self.p_min())

    def _p_to_pq_res(
        self, sp_type: SystemParticipantsEnum, p_series: Series
    ) -> PQResult:
        data = p_series.rename("p").to_frame()
        data["q"] = 0
        return PQResult(sp_type, "flex-signal", "flex-signal", data)

    def hourly_resample(self):
        updated_data = self.data.apply(lambda x: hourly_mean_resample(x))
        return FlexOptionResult(
            self.entity_type, self.input_model, self.name, updated_data
        )

    def add_series(self, series: Series) -> "FlexOptionResult":
        updated_data = self.data.apply(
            lambda p_flex: add_series(p_flex, series, p_flex.name), axis=0
        )
        return FlexOptionResult(
            self.entity_type, self.input_model, self.name, updated_data
        )


@dataclass(frozen=True)
class FlexOptionsResult(ResultDict):
    entities: Dict[str, FlexOptionResult]

    def to_df(self) -> DataFrame:
        return pd.concat(
            [f.data for f in self.entities.values()],
            keys=self.entities.keys(),
            axis=1,
        ).ffill()

    def to_multi_index_df(
        self, participants_res  # type hinting leads to circular import
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
                    for uuid, flex in flex_res.entities.items()
                ]
                flex_midf = pd.concat(flex_dfs, keys=participant_uuids, axis=1)
                flex_midfs[res.entity_type.value] = flex_midf
        return pd.concat(flex_midfs.values(), keys=(flex_midfs.keys()), axis=1).ffill()

    def sum(self) -> FlexOptionResult:
        return FlexOptionResult.sum(list(self.entities.values()))

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
