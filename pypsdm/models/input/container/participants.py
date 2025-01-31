from dataclasses import dataclass
from pathlib import Path
from typing import Union

import pandas as pd
from pandas import Series

from pypsdm.models.enums import EntitiesEnum, SystemParticipantsEnum
from pypsdm.models.input.container.mixins import ContainerMixin
from pypsdm.models.input.entity import Entities
from pypsdm.models.input.node import Nodes
from pypsdm.models.input.participant.bm import BiomassPlants
from pypsdm.models.input.participant.em import EnergyManagementSystems
from pypsdm.models.input.participant.evcs import EvChargingStations
from pypsdm.models.input.participant.evs import ElectricVehicles
from pypsdm.models.input.participant.fixed_feed_in import FixedFeedIns
from pypsdm.models.input.participant.hp import HeatPumps
from pypsdm.models.input.participant.load import Loads
from pypsdm.models.input.participant.pv import PhotovoltaicPowerPlants
from pypsdm.models.input.participant.storage import Storages
from pypsdm.models.input.participant.wec import WindEnergyConverters


@dataclass(frozen=True)
class SystemParticipantsContainer(ContainerMixin):
    ems: EnergyManagementSystems
    loads: Loads
    fixed_feed_ins: FixedFeedIns
    pvs: PhotovoltaicPowerPlants
    biomass_plants: BiomassPlants
    wecs: WindEnergyConverters
    storages: Storages
    evs: ElectricVehicles
    evcs: EvChargingStations
    hps: HeatPumps

    def to_list(self, include_empty=False) -> list[Entities]:
        participants = [
            self.ems,
            self.loads,
            self.fixed_feed_ins,
            self.pvs,
            self.biomass_plants,
            self.wecs,
            self.storages,
            self.evs,
            self.evcs,
            self.hps,
        ]
        return (
            participants
            if include_empty
            else [p for p in participants if not p.data.empty]
        )

    def build_node_participants_map(
        self, nodes: Union[Nodes, list[str]]
    ) -> dict[str, "SystemParticipantsContainer"]:
        uuids = nodes.uuid if isinstance(nodes, Nodes) else nodes
        return {uuid: self.filter_by_nodes(uuid) for uuid in uuids}

    def filter_by_nodes(
        self, node_uuids: str | list[str]
    ) -> "SystemParticipantsContainer":
        loads = self.loads.filter_by_nodes(node_uuids)
        fixed_feed_ins = self.fixed_feed_ins.filter_by_nodes(node_uuids)
        pvs = self.pvs.filter_by_nodes(node_uuids)
        biomass_plants = self.biomass_plants.filter_by_nodes(node_uuids)
        wecs = self.wecs.filter_by_nodes(node_uuids)
        storages = self.storages.filter_by_nodes(node_uuids)
        evs = self.evs.filter_by_nodes(node_uuids)
        evcs = self.evcs.filter_by_nodes(node_uuids)
        hps = self.hps.filter_by_nodes(node_uuids)

        return SystemParticipantsContainer(
            EnergyManagementSystems.create_empty(),
            loads,
            fixed_feed_ins,
            pvs,
            biomass_plants,
            wecs,
            storages,
            evs,
            evcs,
            hps,
        )

    def get_with_enum(self, sp_type: EntitiesEnum) -> Entities | None:
        if sp_type == SystemParticipantsEnum.ENERGY_MANAGEMENT:
            return self.ems
        elif sp_type == SystemParticipantsEnum.LOAD:
            return self.loads
        elif sp_type == SystemParticipantsEnum.BIOMASS_PLANT:
            return self.biomass_plants
        elif sp_type == SystemParticipantsEnum.FIXED_FEED_IN:
            return self.fixed_feed_ins
        elif sp_type == SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT:
            return self.pvs
        elif sp_type == SystemParticipantsEnum.WIND_ENERGY_CONVERTER:
            return self.wecs
        elif sp_type == SystemParticipantsEnum.STORAGE:
            return self.storages
        elif sp_type == SystemParticipantsEnum.EV_CHARGING_STATION:
            return self.evcs
        elif sp_type == SystemParticipantsEnum.ELECTRIC_VEHICLE:
            return self.evs
        elif sp_type == SystemParticipantsEnum.HEAT_PUMP:
            return self.hps
        else:
            return None

    def find_participant(self, uuid: str) -> Series:
        if uuid in self.loads:
            return self.loads.get(uuid)
        elif uuid in self.fixed_feed_ins:
            return self.fixed_feed_ins.get(uuid)
        elif uuid in self.pvs:
            return self.pvs.get(uuid)
        elif uuid in self.wecs:
            return self.wecs.get(uuid)
        elif uuid in self.biomass_plants:
            return self.biomass_plants.get(uuid)
        elif uuid in self.ems:
            return self.ems.get(uuid)
        elif uuid in self.storages:
            return self.storages.get(uuid)
        elif uuid in self.evs:
            return self.evs.get(uuid)
        elif uuid in self.evcs:
            return self.evcs.get(uuid)
        elif uuid in self.hps:
            return self.hps.get(uuid)
        else:
            raise ValueError(
                f"Particpant with uuid {uuid} could not be found among participants."
            )

    def uuids(self):
        return pd.concat(
            [participants.uuid for participants in self.to_list(include_empty=True)]
        )

    def subset(self, uuids):
        return SystemParticipantsContainer(
            self.ems.subset(uuids, intersection=True),
            self.loads.subset(uuids, intersection=True),
            self.fixed_feed_ins.subset(uuids, intersection=True),
            self.pvs.subset(uuids, intersection=True),
            self.biomass_plants.subset(uuids, intersection=True),
            self.wecs.subset(uuids, intersection=True),
            self.storages.subset(uuids, intersection=True),
            self.evs.subset(uuids, intersection=True),
            self.evcs.subset(uuids, intersection=True),
            self.hps.subset(uuids, intersection=True),
        )

    @staticmethod
    def from_csv(
        path: str | Path, delimiter: str | None = None
    ) -> "SystemParticipantsContainer":
        loads = Loads.from_csv(path, delimiter, must_exist=False)
        fixed_feed_ins = FixedFeedIns.from_csv(path, delimiter, must_exist=False)
        pvs = PhotovoltaicPowerPlants.from_csv(path, delimiter, must_exist=False)
        biomass_plants = BiomassPlants.from_csv(path, delimiter, must_exist=False)
        wecs = WindEnergyConverters.from_csv(path, delimiter, must_exist=False)
        storages = Storages.from_csv(path, delimiter, must_exist=False)
        ems = EnergyManagementSystems.from_csv(path, delimiter, must_exist=False)
        evs = ElectricVehicles.from_csv(path, delimiter, must_exist=False)
        evcs = EvChargingStations.from_csv(path, delimiter, must_exist=False)
        hps = HeatPumps.from_csv(path, delimiter, must_exist=False)
        return SystemParticipantsContainer(
            ems,
            loads,
            fixed_feed_ins,
            pvs,
            biomass_plants,
            wecs,
            storages,
            evs,
            evcs,
            hps,
        )

    @classmethod
    def create(
        cls,
        ems=EnergyManagementSystems.create_empty(),
        loads=Loads.create_empty(),
        fixed_feed_ins=FixedFeedIns.create_empty(),
        pvs=PhotovoltaicPowerPlants.create_empty(),
        bms=BiomassPlants.create_empty(),
        wecs=WindEnergyConverters.create_empty(),
        storages=Storages.create_empty(),
        evs=ElectricVehicles.create_empty(),
        evcs=EvChargingStations.create_empty(),
        hps=HeatPumps.create_empty(),
    ):
        return cls(
            ems=ems,
            loads=loads,
            fixed_feed_ins=fixed_feed_ins,
            pvs=pvs,
            biomass_plants=bms,
            wecs=wecs,
            storages=storages,
            evs=evs,
            evcs=evcs,
            hps=hps,
        )

    @classmethod
    def empty(cls):
        return cls(
            EnergyManagementSystems.create_empty(),
            Loads.create_empty(),
            FixedFeedIns.create_empty(),
            PhotovoltaicPowerPlants.create_empty(),
            BiomassPlants.create_empty(),
            WindEnergyConverters.create_empty(),
            Storages.create_empty(),
            ElectricVehicles.create_empty(),
            EvChargingStations.create_empty(),
            HeatPumps.create_empty(),
        )
