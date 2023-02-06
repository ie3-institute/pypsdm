import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import pandas as pd
from pandas import DataFrame, Series
from pandas.core.groupby import GroupBy

from psdm_analysis.io.utils import csv_to_grpd_df, get_file_path, to_date_time
from psdm_analysis.models.entity import ResultEntities
from psdm_analysis.models.input.enums import RawGridElementsEnum
from psdm_analysis.models.input.node import Nodes
from psdm_analysis.processing.dataframe import filter_data_for_time_interval


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

    @classmethod
    def create_empty(cls, name: str, input_model: str):
        data = pd.DataFrame(columns=cls.attributes())
        cls(name, input_model, -1, data)

    @classmethod
    def build(cls, uuid: str, data: DataFrame, name: str = "") -> "NodeResult":
        if "time" in data.columns:
            data["time"] = data["time"].apply(
                lambda date_string: to_date_time(date_string)
            )
            data = data.set_index("time", drop=True)
        return cls(RawGridElementsEnum.NODE, name, uuid, data)

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

    def filter_for_time_interval(self, start: datetime, end: datetime):
        filtered_data = filter_data_for_time_interval(self.data, start, end)
        return NodeResult.build(self.input_model, filtered_data, self.name)

    @property
    def v_mag(self) -> Series:
        return self.data["v_mag"]

    @property
    def v_ang(self) -> Series:
        return self.data["v_ang"]

    @property
    def start(self) -> datetime:
        return self.data.iloc[0].name

    @property
    def end(self) -> datetime:
        return self.data.iloc[-1].name


# TODO: This should extend ResultDict. Check the type for conformity and make adjustments.
@dataclass(frozen=True)
class NodesResult:
    nodes: Dict[str, NodeResult]

    def __len__(self):
        return len(self.nodes)

    def uuids(self):
        return self.nodes.keys()

    @classmethod
    def from_csv(cls, simulation_data_path: str, delimiter: str, nodes: Nodes = None):
        file_path = get_file_path(simulation_data_path, "node_res.csv")
        if file_path.exists():
            node_data = csv_to_grpd_df("node_res.csv", simulation_data_path, delimiter)
            if not node_data:
                return cls.create_empty()
            return cls(
                node_data.apply(
                    lambda grp: cls.__build_node_result(grp, nodes)
                ).to_dict()
            )
        else:
            logging.warning(f"No nodes result in {str(file_path)}")
            return cls(dict())

    @staticmethod
    def __build_node_result(grp: GroupBy, nodes: Nodes):

        node_id = nodes.get(grp.name)["id"] if nodes else ""
        return NodeResult.build(grp.name, grp.drop(columns=["input_model"]), node_id)

    def get_node_uuid_dropdwon_options(self):
        uuids = self.nodes.keys()
        return [{"label": uuid, "value": uuid} for uuid in uuids]

    def filter_for_time_interval(self, start: datetime, end: datetime):
        return NodesResult(
            {
                uuid: measurements.filter_for_time_interval(start, end)
                for uuid, measurements in self.nodes.items()
            }
        )

    def v_mags(self) -> DataFrame:
        return pd.concat(
            [
                node_res.v_mag.rename(node_res.input_model)
                for node_res in self.nodes.values()
            ],
            axis=1,
        )

    def v_angs(self) -> DataFrame:
        return pd.concat(
            [
                node_res.v_ang.rename(node_res.input_model)
                for node_res in self.nodes.values()
            ],
            axis=1,
        )

    def v_mag_describe(self) -> DataFrame:
        return self._describe(self.v_mags())

    def v_ang_describe(self) -> DataFrame:
        return self._describe(self.v_angs())

    @staticmethod
    def _describe(data: DataFrame):
        return data.describe().transpose()

    @classmethod
    def create_empty(cls):
        return cls(dict())
