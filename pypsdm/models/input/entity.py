from __future__ import annotations

import copy
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, List, Self, Tuple, Type, TypeVar, Union

import pandas as pd
from pandas import DataFrame, Series

from pypsdm.errors import ComparisonError
from pypsdm.io import utils
from pypsdm.io.utils import bool_converter, df_to_csv, read_csv
from pypsdm.models.enums import (
    EntitiesEnum,
    RawGridElementsEnum,
    SystemParticipantsEnum,
)
from pypsdm.processing.dataframe import compare_dfs

if TYPE_CHECKING:
    from pypsdm.models.input.node import Nodes

pd.set_option("mode.copy_on_write", True)
EntityType = TypeVar("EntityType", bound="Entities")


@dataclass(frozen=True)
class Entities(ABC):
    """
    Entities is the abstract base class for all input entity models.
    At it's core all data can be retrieved by accessing the data attribute which returns a pandas DataFrame.
    Every row corresponds to one entity, indexed with their uuid.
    Attribute columns can be accessed by their respectively named property methods.

    Args:
        data: The data of the entities.
    """

    data: DataFrame

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return self.data

    def __contains__(self, uuid: str):
        return uuid in self.data.index

    def __add__(self: EntityType, other: EntityType) -> EntityType:
        """
        Concatenates two Entities instances.

        Args:
            other: The other Entities instance to concatenate with.

        Returns:
            The concatenated Entities instance.
        """

        if not isinstance(other, type(self)):
            raise TypeError(
                f"The two Entities instances must be of the same type. Received {type(self)} and {type(other)}"
            )

        columns_diff = set(self.data.columns).symmetric_difference(other.data.columns)
        if len(columns_diff) > 0 and columns_diff.issubset(self.attributes()):
            logging.warning(
                "The two Entities instances have different columns: %s", columns_diff
            )
        return type(self)(pd.concat([self.data, other.data]))

    def __sub__(self: EntityType, other: Union[EntityType, List[str]]) -> EntityType:
        """
        Subtacts the entities with the given uuids from the Entities instance.

        Args:
            other: The other Entities instance or a list of uuids to subtract.

        Returns:
            A new Entities instance with the uuids removed.
        """

        if isinstance(other, Entities):
            indices_to_remove = other.data.index
        elif isinstance(other, list) and all(isinstance(index, str) for index in other):
            indices_to_remove = other
        else:
            raise TypeError("other must be an Entities instance or a list of strings")

        if not set(indices_to_remove).issubset(self.data.index):
            raise ValueError(
                f"All indices to remove must exist in the current Entities instance: {set(indices_to_remove) - set(self.data.index)}"
            )

        return type(self)(self.data.drop(indices_to_remove))

    @property
    def uuid(self) -> Series:
        """
        Returns: The uuids of the entities.
        """
        return self.data.index.to_series()

    @property
    def id(self) -> Series:
        """
        Returns: The ids of the entities.
        """
        return self.data["id"]

    @property
    def operates_from(self) -> Series:
        """
        Returns: The operaton start time of the entities.
        """
        return self.data["operates_from"]

    @property
    def operates_until(self) -> Series:
        """
        Returns: The operaton end time of the entities.
        """
        return self.data["operates_until"]

    @property
    def operator(self) -> Series:
        """
        Returns: The operator of the entities.
        """
        return self.data["operator"]

    @property
    @abstractmethod
    def node(self) -> Series:
        """
        Returns: The nodes to which the entities are connected.
        """
        pass

    def get(self, uuid: str) -> Series:
        """
        Returns the entity information of the entitiy with the given uuid.

        Args:
            uuid: The uuid of the entity.

        Returns:
            Row (Series) of the corresponding entity information.
        """
        return self.data.loc[uuid]

    def subset(
        self: EntityType,
        uuids: Union[list[str], Series, set[str], str],
        intersection: bool = False,
    ) -> EntityType:
        """
        Creates a subset of the Entities instance with the given uuids. By default it expects all uuids to be
        contained within the Entities. If intersection is set to True, it returns the Entities subset of uuids which are
        present in the Entities instance.

        Args:
            uuids: The uuids to subset.

        Returns:
            A new instance with the subset of entities.
        """
        if isinstance(uuids, str):
            uuids = [uuids]
        if intersection:
            intersection = list(set(self.uuid) & set(uuids))
            return type(self)(self.data.loc[intersection])
        if isinstance(uuids, set):
            uuids = list(uuids)
        try:
            return type(self)(self.data.loc[uuids])
        except KeyError as e:
            not_found = set(uuids) - set(self.data.index)
            raise KeyError(
                f"uuids must be a subset of the current Entities instance. The following uuids couldn't be found: {not_found}"
            ) from e

    def subset_id(self: EntityType, ids: Union[list[str], set[str], str]) -> EntityType:
        """
        Creates a subset of the Entities instance with the given ids.

        Args:
            ids: The ids to subset.

        Returns:
            A new instance with the subset of entities.
        """
        if isinstance(ids, str):
            ids = [ids]
        elif isinstance(ids, set):
            ids = list(ids)
        return type(self)(self.data[self.data["id"].isin(ids)])

    def subset_split(
        self: EntityType, uuids: Union[list[str], Series, set[str], str]
    ) -> Tuple[EntityType, EntityType]:
        """
        Returns the subset of entities as well as the remaining instances.

        Args:
            uuids: The uuids to subset.

        Returns:
            A tuple of the subset and the remaining entities.
        """
        rmd = set(self.uuid) - set(uuids)
        return self.subset(uuids), self.subset(list(rmd))

    def filter_by_nodes(
        self: EntityType, nodes: Union[str, list[str], set[str]]
    ) -> EntityType:
        """
        Filters for all entities which are connected to one of th given nodes.

        Args:
            nodes: The nodes to filter by, represented by their uuids.

        Returns:
            A new Entities instance with the filtered entities.
        """
        if isinstance(nodes, str):
            nodes = [nodes]
        data = self.data[self.node.isin(nodes)]
        return type(self)(data)

    def find_nodes(self, nodes: Nodes) -> Nodes:
        return nodes.subset(self.node.to_list())

    def to_csv(self, path: str, mkdirs=False, delimiter: str = ","):
        # local import to avoid circular imports
        from pypsdm.models.input.mixins import HasTypeMixin
        from pypsdm.models.input.participant.em import EnergyManagementSystems

        # Don't write empty entities
        if not self:
            return

        data = self.data.copy()
        if isinstance(self, EnergyManagementSystems):
            data["connected_assets"] = self.connected_assets.apply(
                lambda x: f"{' '.join(x)}"
            )
        if isinstance(self, HasTypeMixin):
            HasTypeMixin.to_csv(self, path, mkdirs, delimiter)
        else:
            if self.additional_attributes():
                additional_attributes = set(self.additional_attributes())
                additional_not_in_data = additional_attributes - set(data.columns)
                if additional_not_in_data:
                    logging.warning(
                        f"The following additional attributese were not found in the data: \n"
                        f"{additional_not_in_data}.\n"
                        "This might be due to not using the Entities.preprocessing() method "
                        "when building the data."
                    )
                    additional_attributes = (
                        additional_attributes - additional_not_in_data
                    )
                data = data.drop(columns=list(additional_attributes))
            df_to_csv(
                data,
                path,
                self.get_enum().get_csv_input_file_name(),
                mkdirs=mkdirs,
                delimiter=delimiter,
            )

    def compare(self, other) -> None:
        """
        Compares the current Entities instance with another Entities instance.

        Args:
            other: The other Entities instance to compare with.

        Returns:
            None
        """
        if not isinstance(other, type(self)):
            raise ComparisonError(
                f"Type of self {type(self)} != type of other {type(other)}"
            )

        try:
            compare_dfs(self.data, other.data)
        except AssertionError as e:
            raise ComparisonError(
                f"{self.get_enum().get_plot_name()} entities are not equal.",
                differences=[(type(self), str(e))],
            )

    def copy(
        self: EntityType,
        deep=True,
        **changes,
    ) -> EntityType:
        """
        Creates a copy of the current Entities instance.
        By default does a deep copy of all data and replaces the given changes.
        When deep is false, only the references to the data of the non-changed attribtues are copied.

        Args:
            deep: Whether to do a deep copy of the data.
            **changes: The changes to apply to the copy.

        Returns:
            The copy of the current Entities instance.
        """
        to_copy = copy.deepcopy(self) if deep else self
        return replace(to_copy, **changes)

    @classmethod
    def from_csv(cls: Type[Self], path: str, delimiter: str | None = None) -> Self:
        """
        Reads the entity data from a csv file.

        Args:
            path: The path to the csv file.
            delimiter: The delimiter of the csv file.

        Returns:
           The corresponding entities object.
        """
        return cls._from_csv(path, cls.get_enum(), delimiter)

    @classmethod
    def _from_csv(
        cls: Type[Self], path: str, entity: EntitiesEnum, delimiter: str | None = None
    ) -> Self:
        file_path = utils.get_file_path(path, entity.get_csv_input_file_name())
        if os.path.exists(file_path):
            return cls(Entities._data_from_csv(entity, path, delimiter))
        else:
            logging.debug(
                "There is no file named: "
                + str(file_path)
                + ". No "
                + entity.value
                + " entities are loaded."
            )
            return cls.create_empty()

    @classmethod
    def _data_from_csv(
        cls, entity: EntitiesEnum, path: str | Path, delimiter: str | None = None
    ) -> DataFrame:
        data = read_csv(path, entity.get_csv_input_file_name(), delimiter)

        bool_cols = cls.bool_attributes()
        for col in bool_cols:
            try:
                data[col] = data[col].apply(lambda x: bool_converter(x))
                data[col] = data[col].astype(bool)
            except ValueError as e:
                logging.error(
                    f"Could not convert column {col} to bool. "
                    f"Please check the values in the csv file. "
                    f"Error: {e}"
                )

        if entity.has_type():
            # TODO: Capture nonexistent type
            type_data = read_csv(path, entity.get_type_file_name(), delimiter)
            data = (
                data.merge(
                    type_data, left_on="type", right_on="uuid", suffixes=("", "_type")
                )
                .rename(columns={"id_type": "type_id", "uuid_type": "type_uuid"})
                .drop(columns=["type"])
            )

        data = cls.preprocessing(entity, data)

        try:
            return data.set_index("uuid")
        except KeyError as e:
            raise KeyError(
                "Column 'uuid' not found. This might be due to wrong csv delimiter!", e
            )

    @staticmethod
    def preprocessing(entity: EntitiesEnum, data: DataFrame) -> DataFrame:
        """
        We perform some data transformations on the data wich make them easier to handle.
        Additional columns we add are droppen when persisting the data.
        """

        # special data transformations
        match entity:
            # for raw grid elements
            # ---------------------
            case RawGridElementsEnum.NODE:
                data["longitude"] = data["geo_position"].apply(
                    lambda geo_json: json.loads(geo_json)["coordinates"][0]
                )
                data["latitude"] = data["geo_position"].apply(
                    lambda geo_json: json.loads(geo_json)["coordinates"][1]
                )

            # for system participants
            # -----------------------
            case SystemParticipantsEnum.ENERGY_MANAGEMENT:
                data["connected_assets"] = data["connected_assets"].apply(
                    lambda x: x.split(" ")
                )
            case SystemParticipantsEnum.EV_CHARGING_STATION:
                from pypsdm.models.input.participant.charging import (
                    parse_evcs_type_info,
                )

                type_data = data["type"].apply(
                    lambda type_str: parse_evcs_type_info(type_str)
                )
                data = pd.concat([data, type_data], axis=1)
        return data

    @classmethod
    def create_empty(cls: Type[Self]) -> Self:
        """
        Creates an empty instance of the corresponding entity class.
        """
        data = pd.DataFrame(columns=cls.attributes())
        return cls(data)

    @staticmethod
    @abstractmethod
    def get_enum() -> EntitiesEnum:
        """
        Returns the corresponding entity enum value.
        """
        pass

    @classmethod
    def attributes(cls) -> list[str]:
        """
        Method that should hold all attributes field (transformed to snake_case and case-sensitive)
        of the corresponding PSDM entity
        :return:
        """
        return ["id", "operates_from", "operates_until", "operator"]

    @classmethod
    def additional_attributes(cls) -> list[str]:
        """
        Method that should hold all fields we add to the original PSDM entity.
        See the preprocessing for all actual transformations. These
        are dropped when persisting the data, to keep the data consistent.
        """
        return []

    @staticmethod
    def bool_attributes() -> list[str]:
        """
        Method that should hold all boolean attributes field (transformed to snake_case and case-sensitive)
        of the corresponding PSDM entity. It is mainly used for type casting of the data frame column.
        :return:
        """
        return []
