from abc import ABC
from dataclasses import dataclass

import pandas as pd

from psdm_analysis.models.entity import Entities
from psdm_analysis.models.input.node import Nodes


@dataclass(frozen=True)
class Connector(Entities, ABC):
    @staticmethod
    def attributes() -> list[str]:
        return Entities.attributes() + ["node_a", "node_b", "parallel_devices"]

    @property
    def node_a(self):
        return self.data["node_a"]

    @property
    def node_b(self):
        return self.data["node_b"]

    @property
    def parallel_devices(self):
        return self.data["parallel_devices"]

    def nodes(self):
        return pd.concat([self.node_a, self.node_b])

    def filter_for_node(self, uuid: str):
        data = self.data[(self.node_a == uuid) | (self.node_b == uuid)]
        return type(self)(data)

    def insert_node_id_columns(self, nodes: Nodes) -> None:
        index_to_id = nodes.ids.to_dict()

        if "node_a_id" not in self.data.columns:
            self.data.insert(self.data.columns.get_loc("node_a") + 1, "node_a_id", None)
        self.data["node_a_id"] = self.node_a.map(index_to_id)

        if "node_b_id" not in self.data.columns:
            self.data.insert(self.data.columns.get_loc("node_b") + 1, "node_b_id", None)
        self.data["node_b_id"] = self.node_b.map(index_to_id)
