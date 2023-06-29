import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple, TypeVar, Union

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.io.utils import to_date_time
from psdm_analysis.models.input.entity import EntityType
from psdm_analysis.models.enums import EntitiesEnum, SystemParticipantsEnum
from psdm_analysis.processing.dataframe import filter_data_for_time_interval

ResultType = TypeVar("ResultType", bound="ResultEntities")


@dataclass(frozen=True)
class ResultEntities(ABC):
    """
    Abstract base class for all result entities. Results are time series data, which can be mapped to their respective input entities via `input_model`.
    The time series is event discrete. Which means every state is valid until the next state is reached. The time series data is stored in the `data` attribute.
    Attributes:
        entity_type: The type of the entity.
        input_model: The input model uuid the results belong to.
        name: The id of the entity. Can be None.
        data: Resulting time series data of the entity.
    """

    # todo: type is a reserved keyword -> rename
    entity_type: EntitiesEnum
    input_model: str
    name: Optional[str]
    data: DataFrame

    def __repr__(self):
        return self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, where: Union[slice, datetime, list[datetime]]):
        if isinstance(where, slice):
            start, stop, step = where.start, where.stop, where.step
            if step is not None:
                logging.warning("Step is not supported for slicing. Ignoring it.")
            if not (isinstance(start, datetime) and isinstance(stop, datetime)):
                raise ValueError("Only datetime slicing is supported")
            return self.filter_for_time_interval(start, stop)
        elif isinstance(where, datetime):
            filtered, dt = self._get_data_by_datetime(where)
            data = pd.DataFrame(filtered).T
            return self.build(self.entity_type, self.input_model, data, dt, self.name)
        elif isinstance(where, list):
            filtered = [self._get_data_by_datetime(time)[0] for time in where]
            data = pd.DataFrame(pd.concat(filtered, axis=1)).T
            max_dt = sorted(data.index)[-1]
            return self.build(
                self.entity_type, self.input_model, data, max_dt, name=self.name
            )

    def _get_data_by_datetime(self, dt: datetime) -> Tuple[Series, datetime]:
        if dt > self.data.index[-1]:
            logging.warning(
                "Trying to access data after last time step. Returning last time step."
            )
            return self.data.iloc[-1], self.data.index[-1]
        if dt < self.data.index[0]:
            logging.warning(
                "Trying to access data before first time step. Returning first time step."
            )
            return self.data.iloc[0], self.data.index[0]
        else:
            return self.data.asof(dt), dt

    @staticmethod
    @abstractmethod
    def attributes() -> list[str]:
        """
        Returns a list of all attributes of the corresponding PSDM entity. The attributes correspond to its data columns.
        """
        pass

    @classmethod
    def create_empty(
        cls, entity_type: EntitiesEnum, input_model: str, name: Optional[str] = None
    ) -> ResultType:
        """
        Creates an empty ResultEntities object with the given entity type and optionally name.
        Args:
            entity_type: The entity type of the ResultEntities object.
            input_model: The input model of the ResultEntities object.
            name: The name or id of the corresponding input object. Can be none.
        Returns:
            An empty ResultEntities object.
        """
        data = cls.empty_data()
        return cls(entity_type, input_model, name, data)

    @classmethod
    def empty_data(cls, index=None):
        """
        Returns an empty DataFrame with the attributes as columns.
        """
        return (
            pd.DataFrame(columns=cls.attributes(), index=index)
            if index
            else pd.DataFrame(columns=cls.attributes())
        )

    @classmethod
    def build(
        cls,
        entity_type: EntitiesEnum,
        input_model: str,
        data: DataFrame,
        end: datetime,
        name: Optional[str] = None,
    ) -> "ResultEntities":
        """
        Creates a ResultEntities object from the given data.
        The end time is used to fill the last time step of the data with the end time.
        This is because we have a time discrete simulation, which means the last entry in the data
        is the state of the entity at the end of the simulation.
        Args:
            entity_type: The entity type of the ResultEntities object.
            input_model: The input model for which the result data was calculated.
            data: The data of the ResultEntities object.
            end: The end time of the simulation.
            name: The name or id of the corresponding input object. Can be none.
        """
        if data.empty:
            return cls.create_empty(entity_type, input_model, name)

        if "time" in data.columns:
            data["time"] = data["time"].apply(
                lambda date_string: to_date_time(date_string)
            )
            data = data.set_index("time", drop=True)

        last_state = data.iloc[len(data) - 1]
        if last_state.name != end:
            last_state.name = end
            data = pd.concat([data, DataFrame(last_state).transpose()])
        # todo: deal with duplicate indexes -> take later one
        data = data[~data.index.duplicated(keep="last")]
        data.sort_index(inplace=True)
        return cls(entity_type, input_model, name, data)

    # TODO: Check if end time is in or excluded
    def filter_for_time_interval(
        self, start: datetime, end: datetime
    ) -> "ResultEntities":
        """
        Filters the data for the given time interval. The data can also be filtered via object[datetime:datetime].
        See __getitem__ for more information.
        Args:
            start: The start time of the time interval.
            end: The end time of the time interval.
        Returns:
            A new ResultEntities object with the filtered data.
        """
        filtered_data = filter_data_for_time_interval(self.data, start, end)
        return self.build(
            self.entity_type, self.input_model, filtered_data, end, self.name
        )

    @classmethod
    # todo: find a way for parallel calculation
    def sum(cls, results: list[ResultType]) -> ResultType:
        """
        Sums up the time series data for a list of ResultEntities objects.
        Args:
            results: A list of ResultEntities objects.
        Returns:
            A new ResultEntities object with the summed up data.
        """
        if len(results) == 0:
            return cls.create_empty(SystemParticipantsEnum.PARTICIPANTS_SUM, "", "")
        if len(results) == 1:
            return results[0]
        agg = results[0]
        for result in results[1::]:
            agg += result
        return agg

    def find_input_entity(self, input_model: EntityType) -> EntityType:
        """
        Finds the input entity for the object.
        Args:
            input_model: The input models within which the input entity should be found.
        Returns:
            The filtered input entities.
        """
        if self.entity_type != input_model.get_enum():
            logging.warning("Input model type does not match result type!")
        return input_model.subset([self.input_model])
