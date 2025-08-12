from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Self, Union

from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.input.container.grid import GridContainer
from pypsdm.models.input.container.mixins import ResultContainerMixin
from pypsdm.models.result.grid.congestions import CongestionsResult
from pypsdm.models.result.grid.line import LinesResult
from pypsdm.models.result.grid.node import NodesResult
from pypsdm.models.result.grid.switch import SwitchesResult
from pypsdm.models.result.grid.transformer import Transformers2WResult
from pypsdm.models.ts.base import EntityKey


@dataclass
class RawGridResultContainer(ResultContainerMixin):
    nodes: NodesResult
    lines: LinesResult
    transformers_2w: Transformers2WResult
    switches: SwitchesResult
    congestions: CongestionsResult

    def __init__(self, dct):
        def get_or_empty(key: RawGridElementsEnum, dict_type):
            value = dct.get(key, dict_type.empty())
            if not isinstance(value, dict_type):
                raise ValueError(f"Expected {dict_type} but got {dict_type(value)}")
            if not isinstance(value, dict_type):
                raise ValueError(
                    f"Expected {dict_type} for {key} but got {dict_type(value)}"
                )
            return value

        self.nodes = get_or_empty(RawGridElementsEnum.NODE, NodesResult)
        self.lines = get_or_empty(RawGridElementsEnum.LINE, LinesResult)
        self.transformers_2w = get_or_empty(
            RawGridElementsEnum.TRANSFORMER_2_W, Transformers2WResult
        )
        self.switches = get_or_empty(RawGridElementsEnum.SWITCH, SwitchesResult)
        self.congestions = get_or_empty(
            RawGridElementsEnum.CONGESTION, CongestionsResult
        )

    def __len__(self):
        return sum(len(v) for v in self.to_dict().values())

    def __getitem__(self, slice_val) -> Self:
        if not isinstance(slice_val, slice):
            raise ValueError("Only slicing is supported!")
        start, stop, _ = slice_val.start, slice_val.stop, slice_val.step
        if not (isinstance(start, datetime) and isinstance(stop, datetime)):
            raise ValueError("Only datetime slicing is supported")
        return self.interval(start, stop)

    def to_dict(self, include_empty: bool = False) -> dict:
        res = {
            RawGridElementsEnum.NODE: self.nodes,
            RawGridElementsEnum.LINE: self.lines,
            RawGridElementsEnum.TRANSFORMER_2_W: self.transformers_2w,
            RawGridElementsEnum.SWITCH: self.switches,
            RawGridElementsEnum.CONGESTION: self.congestions,
        }
        if not include_empty:
            res = {k: v for k, v in res.items() if v}
        return res

    def to_list(self, include_empty: bool = False) -> list:
        return [v for v in self.to_dict(include_empty).values()]

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]) -> Self:
        return self.__class__(
            {k: v.filter_by_date_time(time) for k, v in self.to_dict().items()}
        )

    def interval(self, start: datetime, end: datetime) -> Self:
        return self.__class__(
            {k: v.interval(start, end) for k, v in self.to_dict().items()}
        )

    def concat(self, other: "RawGridResultContainer", deep: bool = True, keep="last"):
        """
        Concatenates the data of the two containers, which means concatenating
        the data of their entities.

        NOTE: This only makes sense if the entities indexes are continuous. Given
        that we deal with discrete event data that means that the last state of self
        is valid until the first state of the other. Which would probably not be what
        you want in case the results are separated by a year.

        Args:
            other: The other GridResultContainer object to concatenate with.
            deep: Whether to do a deep copy of the data.
            keep: How to handle duplicate indexes. "last" by default.
        """
        return self.__class__(
            {
                k: v.concat(other.to_dict()[k], deep=deep, keep=keep)
                for k, v in self.to_dict().items()
            }
        )

    def nodal_result(self, node_uuid: str | EntityKey) -> "RawGridResultContainer":
        if node_uuid not in self.nodes:
            return RawGridResultContainer.empty()
        if isinstance(node_uuid, str):
            node_uuid = EntityKey(node_uuid)
        return RawGridResultContainer(
            {
                RawGridElementsEnum.NODE: self.nodes.subset([node_uuid]),
            }
        )

    @classmethod
    def entity_keys(cls):
        return set(cls.empty().to_dict(include_empty=True).keys())

    @classmethod
    def from_csv(
        cls,
        simulation_data_path: str | Path,
        simulation_end: Optional[datetime] = None,
        grid_container: Optional[GridContainer] = None,
        delimiter: Optional[str] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ):
        dct = cls.entities_from_csv(
            simulation_data_path,
            simulation_end,
            grid_container,
            delimiter,
            filter_start,
            filter_end,
        )
        res = RawGridResultContainer(dct)  # type: ignore
        return (
            res if not filter_start else res.interval(filter_start, filter_end)  # type: ignore
        )

    @classmethod
    def empty(cls):
        return cls({})
