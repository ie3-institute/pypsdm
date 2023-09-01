from dataclasses import dataclass

from psdm_analysis.models.input.container.mixins import ContainerMixin
from psdm_analysis.models.input.thermal.bus import ThermalBus
from psdm_analysis.models.input.thermal.house import ThermalHouse


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
    def create_empty(cls):
        return cls(ThermalBus.create_empty(), ThermalHouse.create_empty())
