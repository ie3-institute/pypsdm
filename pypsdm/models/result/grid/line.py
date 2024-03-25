from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import pandas as pd

from pypsdm.models.result.grid.connector import ConnectorResult, ConnectorsResult

if TYPE_CHECKING:
    from pypsdm.models.input.connector.lines import Lines


@dataclass(frozen=True)
class LineResult(ConnectorResult):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def utilisation(
        self, i_max_src: Lines | float, side: Literal["a", "b"] = "a"
    ) -> pd.Series:
        if isinstance(i_max_src, Lines):
            line = i_max_src.subset(self.input_model)
            line_i_max = line.i_max.iloc[0]
        elif isinstance(i_max_src, (int, float)):
            line_i_max = i_max_src
        else:
            raise ValueError(
                f"line_i_max_src should be either float or Lines, got {type(i_max_src)}"
            )
        if side == "a":
            i = self.i_a_complex
        elif side == "b":
            i = self.i_b_complex
        else:
            raise ValueError(f"Invalid side: {side}. Should be 'a' or 'b'.")
        return i.abs() / line_i_max


@dataclass(frozen=True)
class LinesResult(ConnectorsResult):
    entities: dict[str, LineResult]

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    def utilisation(self, lines: Lines, side: Literal["a", "b"] = "a") -> pd.DataFrame:
        if not self.entities.values():
            return pd.DataFrame()

        data = pd.DataFrame(
            {
                line_uuid: line.utilisation(lines, side)
                for line_uuid, line in self.entities.items()
            }
        ).sort_index()

        return data
