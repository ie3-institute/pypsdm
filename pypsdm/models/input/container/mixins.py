from __future__ import annotations

import concurrent.futures
import copy
import os
from abc import ABC, abstractmethod
from dataclasses import replace
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Self, Tuple

from loguru import logger

from pypsdm.errors import ComparisonError
from pypsdm.io.utils import check_filter
from pypsdm.models.enums import EntitiesEnum

if TYPE_CHECKING:
    from pypsdm.models.input.container.grid import GridContainer
    from pypsdm.models.result.participant.dict import EntitiesResultDictMixin


class ContainerMixin(ABC):
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        for a, b in zip(
            self.to_list(include_empty=True), other.to_list(include_empty=True)
        ):
            if a != b:
                return False
        return True

    def __bool__(self):
        return len(self.to_list(include_empty=False)) > 0

    @abstractmethod
    def to_list(self, include_empty: bool = False) -> list:
        pass

    @classmethod
    @abstractmethod
    def empty(cls) -> Self:
        pass

    def to_csv(self, path: str, delimiter: str = ",", mkdirs=False):
        for entities in self.to_list():
            try:
                entities.to_csv(path, delimiter=delimiter, mkdirs=mkdirs)
            except Exception as e:
                logger.error(f"Could not write {type(entities)} to {path}. Error: {e}")

    def copy(
        self: Self,
        deep=True,
        **changes,
    ) -> Self:
        """
        Creates a copy of the current container instance.
        By default does a deep copy of all data and replaces the given changes.
        When deep is false, only the references to the data of the non-changed
        attribtues are copied.

        Args:
            deep: Whether to do a deep copy of the data.
            **changes: The changes to apply to the copy.

        Returns:
            The copy of the current container instance.
        """
        to_copy = copy.deepcopy(self) if deep else self
        return replace(to_copy, **changes)

    def compare(self, other) -> None:
        """
        Compares the grid with another grid, and raises an error if they are not equal.
        """
        if not isinstance(other, type(self)):
            raise ComparisonError(
                f"Type of self {type(self)} != type of other {type(other)}"
            )
        errors = []

        list_a = self.to_list(include_empty=True)
        types_a = [type(e) for e in list_a]
        list_b = other.to_list(include_empty=True)
        types_b = [type(e) for e in list_b]

        if types_a != types_b:
            raise ComparisonError(
                f"Non empty container elements differ: {types_a} != {types_b}"
            )

        for a, b in zip(list_a, list_b):
            try:
                a.compare(b)
            except ComparisonError as e:
                errors += [e]

        if errors:
            raise ComparisonError(
                f"Comparison of {type(self)} failed.", differences=errors
            )


class ResultContainerMixin(ContainerMixin):
    @classmethod
    @abstractmethod
    def entity_keys(cls):
        raise NotImplementedError

    @classmethod
    def entities_from_csv(
        cls,
        simulation_data_path: str,
        simulation_end: datetime | None = None,
        grid_container: GridContainer | None = None,
        delimiter: str | None = None,
        filter_start: datetime | None = None,
        filter_end: datetime | None = None,
    ) -> dict[EntitiesEnum, EntitiesResultDictMixin]:
        from pypsdm.models.result.participant.dict import EntitiesResultDictMixin

        res_files = [
            f for f in os.listdir(simulation_data_path) if f.endswith("_res.csv")
        ]
        if len(res_files) == 0:
            raise FileNotFoundError(
                f"No simulation results found in '{simulation_data_path}'."
            )

        entity_values = cls.entity_keys()

        check_filter(filter_start, filter_end)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # warning: Breakpoints in the underlying method might not work when started from ipynb
            pa_from_csv_for_participant = partial(
                EntitiesResultDictMixin.from_csv_for_entity,
                simulation_data_path,
                simulation_end,
                grid_container,
                delimiter=delimiter,
            )
            participant_results = executor.map(
                pa_from_csv_for_participant,
                entity_values,
            )
            participant_result_map = {}
            for participant_result in participant_results:
                if isinstance(participant_result, Tuple):
                    e, participant = participant_result
                    raise IOError(
                        f"Error reading participant result for: {participant}"
                    ) from e
                participant_result_map[participant_result.entity_type()] = (
                    participant_result
                )
        return participant_result_map
