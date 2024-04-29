from dataclasses import dataclass

from pypsdm.models.input.container.mixins import ContainerMixin
from pypsdm.models.input.thermal.bus import ThermalBus
from pypsdm.models.input.thermal.house import ThermalHouse


@dataclass
class ThermalGridContainer(ContainerMixin):
    busses: ThermalBus
    houses: ThermalHouse

    def to_list(self, include_empty: bool = False):
        lst = [self.busses, self.houses]
        if include_empty:
            return lst
        else:
            return [x for x in lst if x]

    @classmethod
    def from_csv(cls, path: str, delimiter: str):
        busses = ThermalBus.from_csv(path, delimiter)
        houses = ThermalHouse.from_csv(path, delimiter)
        return cls(busses, houses)

    @classmethod
    def empty(cls):
        return cls(ThermalBus.create_empty(), ThermalHouse.create_empty())
