import logging
import os
from abc import ABC, abstractmethod

from psdm_analysis.errors import ComparisonError
from psdm_analysis.io.utils import df_to_csv
from psdm_analysis.models.enums import EntitiesEnum
from psdm_analysis.models.input.connector.connector import Connector
from psdm_analysis.models.input.entity import Entities
from psdm_analysis.models.input.participant.participant import SystemParticipants


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
    def create_empty(cls):
        pass

    def to_csv(self, path: str, mkdirs=True, delimiter: str = ","):
        for entities in self.to_list():
            try:
                entities.to_csv(path, delimiter=delimiter, mkdirs=mkdirs)
            except Exception as e:
                logging.error(f"Could not write {type(entities)} to {path}. Error: {e}")

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


class HasTypeMixin(ABC):
    """
    Mixin for entities that have a separate type within the psdm data model.
    This should only be extended as an addition to the Entities class.
    """

    @property
    def type_id(self):
        return self.data["type_id"]

    @property
    def type_uuid(self):
        return self.data["type_uuid"]

    def to_csv(self, path: str, mkdirs=True, delimiter: str = ","):
        if mkdirs:
            os.makedirs(path, exist_ok=True)
        # persist entity_input.csv
        all_entity_attributes = self.attributes(include_type_attrs=False)
        all_entity_attributes.append("type_uuid")
        entity_data = self.data[all_entity_attributes].rename(
            columns={"type_uuid": "type"}
        )
        df_to_csv(
            entity_data,
            path,
            self.get_enum().get_csv_input_file_name(),
            mkdirs=mkdirs,
            delimiter=delimiter,
        )

        # persist entity_type_input.csv
        type_data = (
            self.data[self.type_attributes()]
            .set_index("type_uuid", drop=True)
            .rename(columns={"type_id": "id"})
        )
        df_to_csv(
            type_data.drop_duplicates(),
            path,
            self.get_enum().get_type_file_name(),
            mkdirs=mkdirs,
            delimiter=delimiter,
        )

    @classmethod
    def attributes(cls, include_type_attrs: bool = True) -> list[str]:
        base_attributes = []
        # check if cls is a subclass of SystemParticipants
        if issubclass(cls, SystemParticipants):
            base_attributes += SystemParticipants.attributes()
        elif issubclass(cls, Connector):
            base_attributes += Connector.attributes()
        elif issubclass(cls, Entities):
            base_attributes += Entities.attributes()
        else:
            logging.warning(
                "We expect the type that extends this mixin to be a subclass of a type with attributes!"
            )
        all_entity_attributes = base_attributes + cls.entity_attributes()
        return (
            all_entity_attributes + cls.type_attributes()
            if include_type_attrs
            else all_entity_attributes
        )

    @staticmethod
    @abstractmethod
    def entity_attributes() -> list[str]:
        pass

    @staticmethod
    def type_attributes() -> list[str]:
        return ["type_uuid", "type_id"]

    @staticmethod
    @abstractmethod
    def get_enum() -> EntitiesEnum:
        pass


class SpTypeMixin(HasTypeMixin):
    @property
    def capex(self):
        return self.data["capex"]

    @property
    def opex(self):
        return self.data["opex"]

    @property
    def s_rated(self):
        return self.data["s_rated"]

    @property
    def cos_phi_rated(self):
        return self.data["cos_phi_rated"]

    @staticmethod
    @abstractmethod
    def entity_attributes() -> list[str]:
        pass

    @staticmethod
    def type_attributes() -> list[str]:
        return HasTypeMixin.type_attributes() + [
            "capex",
            "opex",
            "s_rated",
            "cos_phi_rated",
        ]
