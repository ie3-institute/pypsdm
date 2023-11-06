import os
from abc import ABC, abstractmethod

from pypsdm.io.utils import df_to_csv
from pypsdm.models.enums import EntitiesEnum


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

    def to_csv(self, path: str, mkdirs=False, delimiter: str = ","):
        # Don't write empty entities
        if not self:
            return

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
            .drop_duplicates()
            .set_index("type_uuid", drop=True)
            .rename(columns={"type_id": "id"})
        )
        type_data.index.name = "uuid"
        df_to_csv(
            type_data,
            path,
            self.get_enum().get_type_file_name(),
            mkdirs=mkdirs,
            delimiter=delimiter,
        )

    @classmethod
    def attributes(cls, include_type_attrs: bool = True) -> list[str]:
        entity_attributes = cls.entity_attributes()
        return (
            entity_attributes + cls.type_attributes()
            if include_type_attrs
            else entity_attributes
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
