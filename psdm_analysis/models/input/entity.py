from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Tuple, TypeVar, Union

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.io import utils
from psdm_analysis.io.utils import df_to_csv, read_csv
from psdm_analysis.models.input.enums import (
    EntitiesEnum,
    RawGridElementsEnum,
    SystemParticipantsEnum,
)
from psdm_analysis.models.input.participant.charging import parse_evcs_type_info

if TYPE_CHECKING:
    from psdm_analysis.models.input.node import Nodes

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
            raise TypeError("The two Entities instances must be of the same type")

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
        return self.data.index

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

    def subset(self: EntityType, uuids: Union[list[str], set[str], str]) -> EntityType:
        """
        Creates a subset of the Entities instance with the given uuids.

        Args:
            uuids: The uuids to subset.

        Returns:
            A new instance with the subset of entities.
        """
        if isinstance(uuids, str):
            uuids = [uuids]
        elif isinstance(uuids, set):
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
        self: EntityType, uuids: Union[list[str], set[str], str]
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
        return nodes.subset(self.node)

    def to_csv(self, path: str, delimiter: str = ","):
        df_to_csv(self.data, path, self.get_enum().get_csv_input_file_name(), delimiter)

    @classmethod
    def from_csv(cls: EntityType, path: str, delimiter: str) -> EntityType:
        """
        Reads the entity data from a csv file.

        Args:
            path: The path to the csv file.
            delimiter: The delimiter of the csv file.

        Returns:
           The corresponding entities object.
        """
        return cls._from_csv(path, delimiter, cls.get_enum())

    @classmethod
    def _from_csv(cls, path: str, delimiter: str, entity: EntitiesEnum):
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
        cls, entity: EntitiesEnum, path: str, delimiter: str
    ) -> DataFrame:
        data = read_csv(path, entity.get_csv_input_file_name(), delimiter)
        if entity.has_type():
            type_data = read_csv(path, entity.get_type_file_name(), delimiter)
            data = data.merge(
                type_data, left_on="type", right_on="uuid", suffixes=("", "_type")
            ).rename(columns={"id_type": "type_id", "uuid_type": "type_uuid"})
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
                type_data = data["type"].apply(
                    lambda type_str: parse_evcs_type_info(type_str)
                )
                data = pd.concat([data, type_data])

        try:
            return data.set_index("uuid")
        except KeyError as e:
            raise KeyError(
                "Column 'uuid' not found. This might be due to wrong csv delimiter!", e
            )

    @classmethod
    def create_empty(cls: EntityType) -> EntityType:
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

    @staticmethod
    def attributes() -> List[str]:
        """
        Method that should hold all attributes field (transformed to snake_case and case-sensitive)
        of the corresponding PSDM entity
        :return:
        """
        return ["uuid", "id", "operates_from", "operates_until", "operator"]
