from dataclasses import dataclass

import pandas as pd

from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.input.participant.bm import BiomassPlants
from psdm_analysis.models.input.participant.em import EnergyManagementSystems
from psdm_analysis.models.input.participant.evcs import EvChargingStations
from psdm_analysis.models.input.participant.evs import ElectricVehicles
from psdm_analysis.models.input.participant.fixed_feed_in import FixedFeedIns
from psdm_analysis.models.input.participant.hp import HeatPumps
from psdm_analysis.models.input.participant.load import Loads
from psdm_analysis.models.input.participant.pv import PhotovoltaicPowerPlants
from psdm_analysis.models.input.participant.storage import Storages
from psdm_analysis.models.input.participant.wec import WindEnergyConverters


@dataclass(frozen=True)
class SystemParticipantsContainer:
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

    @staticmethod
    def from_csv(path: str, delimiter: str) -> "SystemParticipantsContainer":
        loads = Loads.from_csv(path, delimiter)
        fixed_feed_ins = FixedFeedIns.from_csv(path, delimiter)
        pvs = PhotovoltaicPowerPlants.from_csv(path, delimiter)
        biomass_plants = BiomassPlants.from_csv(path, delimiter)
        wecs = WindEnergyConverters.from_csv(path, delimiter)
        storages = Storages.from_csv(path, delimiter)
        ems = EnergyManagementSystems.from_csv(path, delimiter)
        evs = ElectricVehicles.from_csv(path, delimiter)
        evcs = EvChargingStations.from_csv(path, delimiter)
        hps = HeatPumps.from_csv(path, delimiter)
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

    # todo: implement
    def to_list(self):
        return [
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

    def filter_by_node(self, node_uuid: str):
        loads = self.loads.filer_for_node(node_uuid)
        fixed_feed_ins = self.fixed_feed_ins.filer_for_node(node_uuid)
        pvs = self.pvs.filer_for_node(node_uuid)
        biomass_plants = self.biomass_plants.filer_for_node(node_uuid)
        wecs = self.wecs.filer_for_node(node_uuid)
        storages = self.storages.filer_for_node(node_uuid)
        ems = self.ems.filer_for_node(node_uuid)
        evs = self.evs.filer_for_node(node_uuid)
        evcs = self.evcs.filer_for_node(node_uuid)
        hps = self.hps.filer_for_node(node_uuid)
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

    def get_participants(self, sp_type: SystemParticipantsEnum):
        if sp_type == SystemParticipantsEnum.ENERGY_MANAGEMENT:
            return self.ems
        elif sp_type == SystemParticipantsEnum.LOAD:
            return self.loads
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
        elif sp_type == SystemParticipantsEnum.HEATP_PUMP:
            return self.hps
        else:
            raise ValueError(
                f"No return value for system participant of type: {sp_type}"
            )

    def find_participant(self, uuid: str):
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
            [participants.uuids().to_series() for participants in self.to_list()]
        )

    def subset(self, uuids):
        return SystemParticipantsContainer(
            self.ems.subset(uuids),
            self.loads.subset(uuids),
            self.fixed_feed_ins.subset(uuids),
            self.pvs.subset(uuids),
            self.wecs.subset(uuids),
            self.biomass_plants.subset(uuids),
            self.storages.subset(uuids),
            self.evs.subset(uuids),
            self.evcs.subset(uuids),
            self.hps.subset(uuids),
        )
