import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import pandas as pd
from pandas import DataFrame, Series

from psdm_analysis.io.utils import csv_to_grpd_df, get_file_path
from psdm_analysis.models.entity import ResultEntities
from psdm_analysis.models.input.enums import RawGridElementsEnum
from psdm_analysis.models.result.participant.dict import ResultDict


@dataclass(frozen=True)
class NodeResult(ResultEntities):
    def __eq__(self, other):
        if not isinstance(other, NodeResult):
            return False
        return (
            (self.input_model == other.input_model)
            & (self.name == other.name)
            & (self.data.equals(other.data))
        )

    @staticmethod
    def attributes() -> List[str]:
        return ["v_ang", "v_mag"]

    # todo: fix me
    @staticmethod
    def build_from_nominal_data(
        name,
        uuid: str,
        data: DataFrame,
        rated_voltage: float,
        resolution: int,
    ) -> "NodeResult":
        data["v_mag"] = data["v_mag"].divide(rated_voltage)
        return NodeResult(name, uuid, data)

    @property
    def v_mag(self) -> Series:
        return self.data["v_mag"]

    @property
    def v_ang(self) -> Series:
        return self.data["v_ang"]


@dataclass(frozen=True)
class NodesResult(ResultDict):
    entities: Dict[str, NodeResult]

    def uuids(self):
        return self.entities.keys()

    @classmethod
    def from_csv(
        cls,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime,
    ):
        file_path = get_file_path(simulation_data_path, "node_res.csv")
        if file_path.exists():
            node_data = csv_to_grpd_df("node_res.csv", simulation_data_path, delimiter)
            if not node_data:
                return cls.create_empty(RawGridElementsEnum.NODE)
            return cls(
                RawGridElementsEnum.NODE,
                node_data.apply(
                    lambda grp: NodeResult.build(
                        RawGridElementsEnum.NODE,
                        grp.name,
                        grp.drop(columns=["input_model"]),
                        simulation_end,
                    )
                ).to_dict(),
            )
        else:
            logging.warning(f"No nodes result in {str(file_path)}")
            return cls(RawGridElementsEnum.NODE, dict())

    @property
    def v_mag(self) -> DataFrame:
        return pd.concat(
            [
                node_res.v_mag.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        )

    @property
    def v_ang(self) -> DataFrame:
        return pd.concat(
            [
                node_res.v_ang.rename(node_res.input_model)
                for node_res in self.entities.values()
            ],
            axis=1,
        )

    def v_mag_describe(self) -> DataFrame:
        return self._describe(self.v_mag)

    def v_ang_describe(self) -> DataFrame:
        return self._describe(self.v_ang)

    @staticmethod
    def _describe(data: DataFrame):
        return data.describe().transpose()
