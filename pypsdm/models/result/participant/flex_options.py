from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from typing import List, Self, Sequence

import pandas as pd
from pandas import DataFrame, Series

from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.result.participant.dict import EntitiesResultDictMixin
from pypsdm.models.ts.base import EntityKey, TimeSeries, TimeSeriesDict
from pypsdm.models.ts.types import ComplexPower
from pypsdm.processing.dataframe import add_df
from pypsdm.processing.series import hourly_mean_resample


@dataclass
class FlexOption(TimeSeries):

    def __init__(self, data: pd.DataFrame, end: datetime | None = None):
        super().__init__(data, end)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def __add__(self, other: "FlexOption"):
        data = add_df(self.data, other.data)
        return FlexOption(
            data,
        )

    def p_max(self):
        return self.data["p_max"]

    def p_min(self):
        return self.data["p_min"]

    def p_ref(self):
        return self.data["p_ref"]

    def p_max_as_power(self) -> ComplexPower:
        return self._p_to_pq_res(self.p_max())

    def p_ref_as_power(self) -> ComplexPower:
        return self._p_to_pq_res(self.p_ref())

    def p_min_as_pq(self) -> ComplexPower:
        return self._p_to_pq_res(self.p_min())

    def _p_to_pq_res(self, p_series: Series) -> ComplexPower:
        data = p_series.rename("p").to_frame()
        data["q"] = 0
        return ComplexPower(data)

    def hourly_resample(self):
        updated_data = self.data.apply(lambda x: hourly_mean_resample(x))
        return FlexOption(updated_data)  # type: ignore

    @staticmethod
    def attributes() -> List[str]:
        return ["p_max", "p_min", "p_ref"]

    @classmethod
    # TODO: find a way for parallel calculation
    def sum(cls, results: Sequence[Self]) -> "FlexOption":
        if len(results) == 0:
            return cls.empty()
        if len(results) == 1:
            return results[0]
        return reduce(lambda a, b: a + b, results)


class FlexOptionsDict(TimeSeriesDict[EntityKey, FlexOption], EntitiesResultDictMixin):

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def to_df(self) -> DataFrame:
        return pd.concat(
            [f.data for f in self.values()],
            keys=self.keys(),
            axis=1,
        ).ffill()

    def to_multi_index_df(self, participants_res) -> DataFrame:
        flex_midfs = {}
        for res in participants_res.to_list():
            uuids = res.participants.keys()
            flex_res = self.subset(uuids)
            if flex_res:
                flex_dfs = []
                participant_uuids = []
                [
                    (participant_uuids.append(uuid), flex_dfs.append(flex.data))
                    for uuid, flex in flex_res.items()
                ]
                flex_midf = pd.concat(flex_dfs, keys=participant_uuids, axis=1)
                flex_midfs[res.entity_type.value] = flex_midf
        return pd.concat(flex_midfs.values(), keys=(flex_midfs.keys()), axis=1).ffill()

    def sum(self) -> FlexOption:
        return FlexOption.sum(list(self.values()))

    @classmethod
    def entity_type(cls):
        return SystemParticipantsEnum.FLEX_OPTIONS
