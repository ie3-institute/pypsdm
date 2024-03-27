from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Type

import pandas as pd
from pandas import DataFrame

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.input.entity import Entities
from pypsdm.models.result.entity import ResultEntity
from pypsdm.models.result.participant.dict import ResultDict, ResultDictType


@dataclass(frozen=True)
class SwitchResult(ResultEntity):
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


class SwitchesResult(ResultDict):

    def __init__(self, data: dict[str, SwitchResult]):
        super().__init__(RawGridElementsEnum.SWITCH, data)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @property
    def closed(self) -> DataFrame:
        if not self:
            return pd.DataFrame()
        return pd.concat(
            [
                switch_res.closed.rename(switch_res.input_model)
                for switch_res in self.values()
            ],
            axis=1,
        )

    @classmethod
    def from_csv(
        cls: Type[ResultDictType],
        simulation_data_path: str,
        delimiter: str | None = None,
        simulation_end: Optional[datetime] = None,
        input_entities: Optional[Entities] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ) -> ResultDictType:
        return super().from_csv(
            RawGridElementsEnum.SWITCH,
            simulation_data_path,
            delimiter,
            simulation_end,
            input_entities,
            filter_start,
            filter_end,
        )
