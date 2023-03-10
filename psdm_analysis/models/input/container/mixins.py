import logging
from abc import ABC, abstractmethod

from psdm_analysis.io import utils
from psdm_analysis.models.entity import Entities
from psdm_analysis.models.input.enums import EntitiesEnum
from psdm_analysis.models.input.participant.participant import SystemParticipants


class ContainerMixin(ABC):
    @abstractmethod
    def to_list(self, include_empty: bool = False) -> list:
        pass

    def to_csv(self, path: str, delimiter: str):
        [e.to_csv(path, delimiter) for e in self.to_list()]


class HasTypeMixin(ABC):
    """
    Mixin for entities that have a separate type within the psdm data model.
    This should only be extended as an addition to the Entities class.
    """

    @staticmethod
    @abstractmethod
    def get_enum() -> EntitiesEnum:
        pass

    @property
    def type_id(self):
        return self.data["type_id"]

    @property
    def type_uuid(self):
        return self.data["type_uuid"]

    def to_csv(self, path: str, delimiter: str = ","):
        all_entity_attributes = self.attributes(include_type_attrs=False)
        all_entity_attributes.append("type_uuid"), all_entity_attributes.remove(
            "uuid"
        )  # uuid is set as index
        entity_data = self.data[all_entity_attributes].rename(
            columns={"type_uuid": "type"}
        )
        entity_path = utils.get_file_path(
            path, self.get_enum().get_csv_input_file_name()
        )
        entity_data.to_csv(entity_path, sep=delimiter, index=True, index_label="uuid")
        type_data = (
            self.data[self.type_attributes()]
            .set_index("type_uuid", drop=True)
            .rename(columns={"type_id": "id"})
        )
        type_path = utils.get_file_path(path, self.get_enum().get_type_file_name())
        type_data.drop_duplicates().to_csv(
            type_path, sep=delimiter, index=True, index_label="uuid"
        )

    @classmethod
    def attributes(cls, include_type_attrs: bool = True) -> [str]:
        base_attributes = []
        # check if cls is a subclass of SystemParticipants
        if issubclass(cls, SystemParticipants):
            base_attributes += SystemParticipants.attributes()
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
    def entity_attributes() -> [str]:
        pass

    @staticmethod
    def type_attributes() -> [str]:
        return ["type_uuid", "type_id"]


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
    def entity_attributes() -> [str]:
        pass

    @staticmethod
    def type_attributes() -> [str]:
        return HasTypeMixin.type_attributes() + [
            "capex",
            "opex",
            "s_rated",
            "cos_phi_rated",
        ]
