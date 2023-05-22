from abc import ABC, abstractmethod
from dataclasses import dataclass

from psdm_analysis.models.entity import Entities
from psdm_analysis.models.input.node import Nodes


@dataclass(frozen=True)
class SystemParticipants(Entities, ABC):
    @staticmethod
    def attributes():
        return Entities.attributes() + ["node", "q_characteristics"]

    def nodes(self):
        return self.data["node"]

    def q_characteristics(self):
        return self.data["q_characteristic"]

    def subset(self, uuids: list[str]):
        data = self.data.loc[self.data.index.intersection(uuids)]
        return type(self)(data)

    def insert_node_id_columns(self, nodes: Nodes) -> None:
        index_to_id = nodes.ids.to_dict()

        if "node_id" not in self.data.columns:
            self.data.insert(self.data.columns.get_loc("node") + 1, "node_id", None)
        self.data["node_id"] = self.nodes().map(index_to_id)


@dataclass(frozen=True)
class SystemParticipantsWithCapacity(SystemParticipants):
    @staticmethod
    @abstractmethod
    def capacity_attribute() -> str:
        pass

    @staticmethod
    def attributes():
        return Entities.attributes() + ["node", "capacity"]

    def capacity(self):
        return self.data[self.capacity_attribute()]
