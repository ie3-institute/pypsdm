import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Type, Self, Union

import pandas as pd
from pandas import DataFrame

from pypsdm import EntitiesEnum, MappingEnum, GridContainer, RawGridElementsEnum, SystemParticipantsEnum
from pypsdm.io import utils
from pypsdm.io.utils import read_csv, df_to_csv

# todo: expand this later
column_schemes: dict[Union[RawGridElementsEnum | SystemParticipantsEnum], str] = {
    SystemParticipantsEnum.LOAD: "pq",
    SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT: "p"
}


class DataTypeEnum(Enum):
    EXT_PRIMARY_INPUT = "primary_input"
    EXT_EM_INPUT = "em_input"
    EXT_GRID_RESULT = "grid_result"
    EXT_PARTICIPANT_RESULT = "participant_result"

def _to_df(entries: list[(str, str,  str, DataTypeEnum)]):
    entry_list = [{"uuid": entry[0], "id": entry[1], "column_scheme": entry[2], "data_type": entry[3].value} for entry in entries]

    try:
        return pd.DataFrame(entry_list).set_index("uuid")
    except KeyError:
        return pd.DataFrame(entry_list)

@dataclass(frozen=False)
class ExtEntityMapping:
    data: DataFrame

    @property
    def uuid(self):
        return self.data["uuid"]

    @property
    def id(self):
        return self.data["id"]

    @property
    def column_scheme(self):
        return self.data["column_scheme"]

    @property
    def data_type(self):
        return self.data["data_type"]


    def add_entry(self, uuid: str, external_id: str, column_scheme: str, data_type: DataTypeEnum):
        field_to_value = {"uuid": uuid, "id": external_id, "column_scheme": column_scheme, "data_type": str(data_type.value)}
        row = pd.DataFrame([field_to_value]).set_index("uuid")
        return ExtEntityMapping(pd.concat([self.data, row], ignore_index=False))

    def add_entries(self, entries: list[(str, str,  str, DataTypeEnum)]):
        rows = _to_df(entries)
        return ExtEntityMapping(pd.concat([self.data, rows], ignore_index=False))

    @staticmethod
    def get_enum() -> EntitiesEnum:
        return MappingEnum.ExtEntity

    def to_csv(self, path: str, mkdirs=False, delimiter: str = ","):
        # local import to avoid circular imports

        # Don't write empty entities
        if not self:
            return

        data = self.data.copy()
        df_to_csv(
            data,
            path,
            self.get_enum().get_csv_input_file_name(),
            mkdirs=mkdirs,
            delimiter=delimiter,
        )

    @classmethod
    def create_from_grid(
            cls: Type[Self],
            grid: GridContainer,
            primary: list[SystemParticipantsEnum],
            em: list[SystemParticipantsEnum],
            result: list[Union[RawGridElementsEnum, SystemParticipantsEnum]]
    ) -> Self:
        primary_inputs = {asset: grid.get_with_enum(asset).uuid.to_list() for asset in primary}
        em_inputs = {asset: grid.get_with_enum(asset).uuid.to_list() for asset in em}
        result_outputs = {asset: grid.get_with_enum(asset).uuid.to_list() for asset in result}

        return cls.from_grid(grid, primary_inputs, em_inputs, result_outputs)


    @classmethod
    def from_grid(
            cls: Type[Self],
            grid: GridContainer,
            primary_inputs: dict[SystemParticipantsEnum, list[str]],
            em_inputs: dict[SystemParticipantsEnum, list[str]],
            result_outputs: dict[Union[RawGridElementsEnum, SystemParticipantsEnum], list[str]]
    ) -> Self:
        entries: list[(str, str,  str, DataTypeEnum)] = []

        for asset, uuids in primary_inputs.items():
            elements = grid.participants.get_with_enum(asset).data
            column_scheme = column_schemes[asset]
            entries += [(uuid, elements.loc[uuid]["id"], column_scheme, DataTypeEnum.EXT_PRIMARY_INPUT) for uuid in uuids]

        for asset, uuids in em_inputs.items():
            elements = grid.participants.get_with_enum(asset).data
            entries += [(uuid, elements.loc[uuid]["id"], "p", DataTypeEnum.EXT_EM_INPUT) for uuid in uuids]

        for result_asset, uuids in result_outputs.items():
            elements = grid.get_with_enum(result_asset).data
            data_type: DataTypeEnum

            if isinstance(result_outputs, RawGridElementsEnum):
                data_type = DataTypeEnum.EXT_GRID_RESULT
            else:
                data_type = DataTypeEnum.EXT_PARTICIPANT_RESULT

            column_scheme = column_schemes[result_asset]
            entries += [(uuid, elements.loc[uuid]["id"], column_scheme, data_type) for uuid in uuids]

        return cls(_to_df(entries))


    @classmethod
    def from_csv(
        cls: Type[Self],
        path: str | Path,
        delimiter: str | None = None,
        must_exist: bool = True,
    ) -> Self:
        entity = cls.get_enum()

        file_path = utils.get_file_path(path, entity.get_csv_input_file_name())
        if os.path.exists(file_path):
            return ExtEntityMapping(read_csv(path, entity.get_csv_input_file_name(), delimiter).set_index("uuid"))
        else:
            if must_exist:
                raise FileNotFoundError(f"File {file_path} does not exist.")
            else:
                return cls.create_empty()


    @classmethod
    def create_empty(cls: Type[Self]) -> Self:
        """
        Creates an empty instance of the corresponding entity class.
        """
        data = pd.DataFrame(columns=["uuid", "id", "column_scheme", "data_type"])
        return cls(data)