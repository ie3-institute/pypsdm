from __future__ import annotations

from typing import Literal

import pandas as pd

from pypsdm.models.enums import EntitiesEnum, RawGridElementsEnum
from pypsdm.models.input.connector.lines import Lines
from pypsdm.models.result.grid.connector import ConnectorCurrentDict
from pypsdm.models.result.participant.dict import EntitiesResultDictMixin
from pypsdm.models.ts.base import EntityKey


class LinesResult(ConnectorCurrentDict[EntityKey], EntitiesResultDictMixin):

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def utilisation(self, lines: Lines, side: Literal["a", "b"] = "a") -> pd.DataFrame:
        if not self.values():
            return pd.DataFrame()

        i_max = lines.i_max
        data = pd.DataFrame(
            {
                line_uuid: line.utilisation(i_max[line_uuid.uuid], side)
                for line_uuid, line in self.items()
            }
        ).sort_index()

        return data

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return RawGridElementsEnum.LINE
