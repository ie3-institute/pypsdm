from abc import abstractmethod
from dataclasses import dataclass

from psdm_analysis.models.entity import Entities


# todo: require system participants enum reference
@dataclass(frozen=True)
class SystemParticipants(Entities):
    @staticmethod
    def attributes():
        return Entities.attributes() + ["node", "q_characteristics"]

    def nodes(self):
        return self.data["node"]

    def q_characteristics(self):
        return self.data["q_characteristic"]

    def filer_for_node(self, uuid: str):
        data = self.data[self.nodes() == str(uuid)]
        return type(self)(data)

    def subset(self, uuids: [str]):
        data = self.data.loc[self.data.index.intersection(uuids)]
        return type(self)(data)


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
