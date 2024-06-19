from dataclasses import dataclass
from datetime import datetime

from pandas import DataFrame

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.result.participant.dict import SubgridResultDictMixin
from pypsdm.models.ts.base import (
    SubGridKey,
    TimeSeries,
    TimeSeriesDict,
    TimeSeriesDictMixin
)


@dataclass
class CongestionResult(TimeSeries):
    def __init__(self, data: DataFrame, end: datetime | None = None):
        super().__init__(data, end)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def __add__(self, _):
        return NotImplemented

    @property
    def vMin(self) -> float:
        return self.data["vMin"].drop_duplicates()[0]

    @property
    def vMax(self) -> float:
        return self.data["vMax"].drop_duplicates()[0]

    @property
    def subnet(self) -> int:
        return self.data["subgrid"].drop_duplicates()[0]

    @property
    def voltage(self):
        return self.data["voltage"]

    @property
    def line(self):
        return self.data["line"]

    @property
    def transformer(self):
        return self.data["transformer"]

    @staticmethod
    def attributes() -> list[str]:
        return ["vMin", "vMax", "subgrid", "voltage", "line", "transformer"]


class CongestionsResult(
    TimeSeriesDict[SubGridKey, CongestionResult],
    TimeSeriesDictMixin,
    SubgridResultDictMixin
):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @property
    def vMin(self) -> DataFrame:
        return self.attr_df("vMin")

    @property
    def vMax(self) -> DataFrame:
        return self.attr_df("vMax")

    @property
    def subnet(self) -> DataFrame:
        return self.attr_df("subgrid")

    @property
    def voltage(self) -> DataFrame:
        return self.attr_df("voltage")

    @property
    def line(self) -> DataFrame:
        return self.attr_df("line")

    @property
    def transformer(self) -> DataFrame:
        return self.attr_df("transformer")

    @classmethod
    def entity_type(cls) -> RawGridElementsEnum:
        return RawGridElementsEnum.SUBGRID
