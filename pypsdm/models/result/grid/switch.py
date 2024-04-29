from dataclasses import dataclass
from datetime import datetime

from pandas import DataFrame

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.participant.dict import EntitiesResultDictMixin
from pypsdm.models.ts.base import (
    EntityKey,
    TimeSeries,
    TimeSeriesDict,
    TimeSeriesDictMixin,
)


@dataclass
class SwitchResult(TimeSeries):
    def __init__(self, data: DataFrame, end: datetime | None = None):
        super().__init__(data, end)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def __add__(self, _):
        return NotImplemented

    @property
    def closed(self):
        return self.data["closed"]

    @staticmethod
    def attributes() -> list[str]:
        return ["closed"]


class SwitchesResult(
    TimeSeriesDict[EntityKey, SwitchResult],
    TimeSeriesDictMixin,
    EntitiesResultDictMixin,
):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def closed(self) -> DataFrame:
        return self.attr_df("closed")

    @classmethod
    def entity_type(cls) -> RawGridElementsEnum:
        return RawGridElementsEnum.SWITCH
