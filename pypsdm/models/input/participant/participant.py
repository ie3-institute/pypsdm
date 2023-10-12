from abc import ABC, abstractmethod
from dataclasses import dataclass

from pypsdm.models.input.entity import Entities
from pypsdm.models.input.node import Nodes


@dataclass(frozen=True)
class SystemParticipants(Entities, ABC):
    @property
    def node(self):
        return self.data["node"]

    @property
    def q_characteristic(self):
        return self.data["q_characteristic"]

    def insert_node_id_columns(self, nodes: Nodes) -> None:
        index_to_id = nodes.id.to_dict()

        if "node_id" not in self.data.columns:
            self.data.insert(self.data.columns.get_loc("node") + 1, "node_id", None)
        self.data["node_id"] = self.node.map(index_to_id)

    @staticmethod
    def attributes():
        return Entities.attributes() + ["node", "q_characteristics"]


@dataclass(frozen=True)
class SystemParticipantsWithCapacity(SystemParticipants):
    def capacity(self):
        return self.data[self.capacity_attribute()]

    @staticmethod
    @abstractmethod
    def capacity_attribute() -> str:
        pass

    @staticmethod
    def attributes():
        return Entities.attributes() + ["node", "capacity"]
