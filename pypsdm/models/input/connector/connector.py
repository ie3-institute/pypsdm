from abc import ABC
from dataclasses import dataclass
from typing import Sequence, TypeVar, Union

import pandas as pd

from pypsdm.models.input.entity import Entities
from pypsdm.models.input.node import Nodes

ConnectorType = TypeVar("ConnectorType", bound="Connector")


@dataclass(frozen=True)
class Connector(Entities, ABC):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @property
    def node_a(self):
        return self.data["node_a"]

    @property
    def node_b(self):
        return self.data["node_b"]

    @property
    def parallel_devices(self):
        return self.data["parallel_devices"]

    @property
    def node(self):
        return pd.concat([self.node_a, self.node_b])

    def filter_by_nodes(
        self: ConnectorType,
        node_uuids: Union[str, Sequence[str] | pd.Series],
        both_in_nodes=False,
    ) -> ConnectorType:
        """
        Returns all connectors that are connected to the given nodes.

        Args:
            node_uuids: List of node uuids to find lines for.
            both_in_nodes: If True, both nodes of the line must be in the given list of nodes.

        Returns:
            ConnectorType: Connectors that are connected to the given nodes.
        """
        if isinstance(node_uuids, str):
            node_uuids = [node_uuids]
        if both_in_nodes:
            data = self.data[
                (self.node_a.isin(node_uuids)) & (self.node_b.isin(node_uuids))
            ]
        else:
            data = self.data[
                (self.node_a.isin(node_uuids)) | (self.node_b.isin(node_uuids))
            ]
        return type(self)(data)

    def filter_by_node_pair(
        self: ConnectorType, node_a_uuid: str, node_b_uuid: str
    ) -> ConnectorType:
        """
        Returns the connector that connects the given nodes. Order of the nodes does not matter.

        Args:
            node_a_uuid (str): UUID of the first node.
            node_b_uuid (str): UUID of the second node.

        Returns:
            Lines: Line that connects the given nodes. Will be empty if no line is found.
        """
        return self.filter_by_nodes([node_a_uuid, node_b_uuid], both_in_nodes=True)

    def insert_node_id_columns(self, nodes: Nodes) -> None:
        index_to_id = nodes.id.to_dict()

        if "node_a_id" not in self.data.columns:
            self.data.insert(self.data.columns.get_loc("node_a") + 1, "node_a_id", None)
        self.data["node_a_id"] = self.node_a.map(index_to_id)

        if "node_b_id" not in self.data.columns:
            self.data.insert(self.data.columns.get_loc("node_b") + 1, "node_b_id", None)
        self.data["node_b_id"] = self.node_b.map(index_to_id)

    @staticmethod
    def attributes() -> list[str]:
        return Entities.attributes() + ["node_a", "node_b", "parallel_devices"]
