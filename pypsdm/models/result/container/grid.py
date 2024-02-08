from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from pypsdm.io.utils import check_filter
from pypsdm.models.input.container.grid import GridContainer
from pypsdm.models.input.container.mixins import ContainerMixin
from pypsdm.models.result.container.participants import ParticipantsResultContainer
from pypsdm.models.result.container.raw_grid import RawGridResultContainer


@dataclass(frozen=True)
class GridResultContainer(ContainerMixin):
    name: str
    raw_grid: RawGridResultContainer
    participants: ParticipantsResultContainer

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @property
    def nodes(self):
        return self.raw_grid.nodes

    @property
    def lines(self):
        return self.raw_grid.lines

    @property
    def transformers_2w(self):
        return self.raw_grid.transformers_2w

    @property
    def switches(self):
        return self.raw_grid.switches

    @property
    def ems(self):
        return self.participants.ems

    @property
    def loads(self):
        return self.participants.loads

    @property
    def fixed_feed_ins(self):
        return self.participants.fixed_feed_ins

    @property
    def pvs(self):
        return self.participants.pvs

    @property
    def wecs(self):
        return self.participants.wecs

    @property
    def storages(self):
        return self.participants.storages

    @property
    def evs(self):
        return self.participants.evs

    @property
    def evcs(self):
        return self.participants.evcs

    @property
    def hps(self):
        return self.participants.hps

    @property
    def flex(self):
        return self.participants.flex

    def __len__(self):
        return +len(self.raw_grid) + len(self.participants)

    # TODO: implement slicing
    def __getitem__(self, slice_val):
        raise NotImplementedError

    def to_list(self, include_empty: bool = False) -> list:
        res = [
            self.nodes,
            self.raw_grid,
            self.participants,
        ]
        return res if include_empty else [r for r in res if r]

    def uuids(self) -> set[str]:
        return set(self.nodes.entities.keys())

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return GridResultContainer(
            self.name,
            self.raw_grid.filter_by_date_time(time),
            self.participants.filter_by_date_time(time),
        )

    def filter_for_time_interval(self, start: datetime, end: datetime):
        return GridResultContainer(
            self.name,
            self.raw_grid.filter_for_time_interval(start, end),
            self.participants.filter_for_time_interval(start, end),
        )

    def concat(self, other: "GridResultContainer", deep: bool = True, keep="last"):
        """
        Concatenates the data of the two containers, which means concatenating
        the data of their entities.

        NOTE: This only makes sense if the entities indexes are continuous. Given
        that we deal with discrete event data that means that the last state of self
        is valid until the first state of other. Which would probably not be what
        you want in case the results are separated by a year.

        Args:
            other: The other GridResultContainer object to concatenate with.
            deep: Whether to do a deep copy of the data.
            keep: How to handle duplicate indexes. "last" by default.
        """
        return GridResultContainer(
            self.name,
            self.raw_grid.concat(other.raw_grid, deep=deep, keep=keep),
            self.participants.concat(other.participants, deep=deep, keep=keep),
        )

    @classmethod
    def from_csv(
        cls,
        name: str,
        simulation_data_path: str,
        delimiter: str | None = None,
        simulation_end: Optional[datetime] = None,
        grid_container: Optional[GridContainer] = None,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ):
        check_filter(filter_start, filter_end)

        raw_grid = RawGridResultContainer.from_csv(
            simulation_data_path,
            delimiter=delimiter,
            simulation_end=simulation_end,
            grid_container=grid_container,
            filter_start=filter_start,
            filter_end=filter_end,
        )

        participants = ParticipantsResultContainer.from_csv(
            simulation_data_path,
            simulation_end,  # type: ignore
            grid_container=grid_container,
            filter_start=filter_start,
            filter_end=filter_end,
            delimiter=delimiter,
        )

        return cls(name, raw_grid, participants)

    @classmethod
    def create_empty(cls):
        return cls(
            name="Empty Container",
            raw_grid=RawGridResultContainer.create_empty(),
            participants=ParticipantsResultContainer.create_empty(),
        )
