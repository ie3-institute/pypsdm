from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from pandas import DataFrame

from pypsdm import EntitiesResultDictMixin
from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.ts.base import (
    EntityKey,
    TimeSeries,
    TimeSeriesDict,
    TimeSeriesDictMixin,
)


class InputModelType(Enum):
    NODE = "node"
    LINE = "line"
    TRANSFORMER_2_W = "transformer_2w"
    TRANSFORMER_3_W = "transformer_3w"


@dataclass
class CongestionResult(TimeSeries):
    def __init__(self, data: DataFrame, end: datetime | None = None):
        super().__init__(data, end)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def __add__(self, _):
        return NotImplemented

    @property
    def subgrid(self) -> int:
        return self.data["subgrid"].drop_duplicates()[0]

    @property
    def input_model_type(self) -> InputModelType:
        match self.data["type"].drop_duplicates()[0]:
            case "node":
                return InputModelType.NODE
            case "line":
                return InputModelType.LINE
            case "transformer_2w":
                return InputModelType.TRANSFORMER_2_W
            case "transformer_3w":
                return InputModelType.TRANSFORMER_3_W

    @property
    def value(self) -> float:
        return self.data["value"].drop_duplicates()[0]

    @property
    def min(self) -> float:
        return self.data["min"].drop_duplicates()[0]

    @property
    def max(self) -> float:
        return self.data["max"].drop_duplicates()[0]

    @staticmethod
    def attributes() -> list[str]:
        return ["subgrid", "type", "value", "min", "max"]


class CongestionsResult(
    TimeSeriesDict[EntityKey, CongestionResult],
    TimeSeriesDictMixin,
    EntitiesResultDictMixin,
):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @property
    def subgrid(self) -> DataFrame:
        return self.attr_df("subgrid")

    @property
    def type(self) -> DataFrame:
        return self.attr_df("type")

    @property
    def value(self) -> DataFrame:
        return self.attr_df("value")

    @property
    def min(self) -> DataFrame:
        return self.attr_df("min")

    @property
    def max(self) -> DataFrame:
        return self.attr_df("max")

    @classmethod
    def entity_type(cls) -> RawGridElementsEnum:
        return RawGridElementsEnum.CONGESTION
