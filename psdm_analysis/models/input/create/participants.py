from uuid import uuid4

import pandas as pd

from psdm_analysis.models.enums import ElectricCurrentType
from psdm_analysis.models.input.create.utils import create_data
from psdm_analysis.models.input.participant import evcs
from psdm_analysis.models.input.participant.em import EnergyManagementSystems
from psdm_analysis.models.input.participant.evcs import EvChargingStations
from psdm_analysis.models.input.participant.evs import ElectricVehicles
from psdm_analysis.models.input.participant.hp import HeatPumps
from psdm_analysis.models.input.participant.load import Loads
from psdm_analysis.models.input.participant.pv import PhotovoltaicPowerPlants
from psdm_analysis.models.input.participant.storage import Storages


def fixed_q_characteristics(cos_phi):
    return f"cosPhiFixed:{{(0.0, {cos_phi})}}"


def create_pvs(data_dict):
    return PhotovoltaicPowerPlants(create_data(data_dict, create_pv_data))


def create_pv_data(
    id,
    node,
    s_rated,
    azimuth,  # South = 0°, West = 90°, East = -90°
    elevation_angle,  # Tilted inclination from horizontal [0°, 90°]
    eta_conv=97,
    cos_phi_rated=0.9,
    albedo=0.21,
    q_characteristics=None,
    k_g=0.9,
    k_t=1,
    market_reaction=False,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
):
    if not uuid:
        uuid = str(uuid4())
    if not q_characteristics:
        q_characteristics = fixed_q_characteristics(cos_phi_rated)
    return pd.Series(
        {
            "id": id,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "node": node,
            "q_characteristics": q_characteristics,
            "s_rated": s_rated,
            "albedo": albedo,
            "azimuth": azimuth,
            "elevation_angle": elevation_angle,
            "eta_conv": eta_conv,
            "k_g": k_g,
            "k_t": k_t,
            "market_reaction": market_reaction,
            "cos_phi_rated": cos_phi_rated,
        }
    ).rename(uuid)


def create_storages(data_dict):
    return Storages(create_data(data_dict, create_storages_data))


def create_storages_data(
    id,
    node,
    e_storage,
    s_rated=None,
    q_characteristics=None,
    behaviour="self",
    type_uuid=None,
    type_id=None,
    capex=0,
    opex=0,
    cos_phi_rated=0.9,
    p_max=None,
    active_power_gradient=100,
    eta=100,  # efficiency of the electrical inverter
    dod=10,  # depth of discharge -> dod% of the capacity can be used
    life_time=9999999,  # permissible hours of full use
    life_cycle=9999999,  # permissible amount of full cycles
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
):
    if not s_rated:
        s_rated = e_storage / 2
    if not q_characteristics:
        q_characteristics = fixed_q_characteristics(cos_phi_rated)
    if not type_uuid:
        type_uuid = str(uuid4())
    if not type_id:
        type_id = f"Type_{id}"
    if not p_max:
        p_max = s_rated
    if not uuid:
        uuid = str(uuid4())
    return pd.Series(
        {
            "id": id,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "node": node,
            "q_characteristics": q_characteristics,
            "type_uuid": type_uuid,
            "type_id": type_id,
            "capex": capex,
            "opex": opex,
            "s_rated": s_rated,
            "cos_phi_rated": cos_phi_rated,
            "p_max": p_max,
            "active_power_gradient": active_power_gradient,
            "e_storage": e_storage,
            "eta": eta,
            "dod": dod,
            "life_time": life_time,
            "life_cycle": life_cycle,
        }
    ).rename(uuid)


def create_electric_vehicles(data_dict):
    return ElectricVehicles(create_data(data_dict, create_electric_vehicles_data))


def create_electric_vehicles_data(
    id,
    node,
    s_rated,
    e_storage,
    e_cons,
    q_characteristics=None,
    type_uuid=None,
    type_id=None,
    capex=0,
    opex=0,
    cos_phi_rated=1,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
):
    if not uuid:
        uuid = str(uuid4())
    if not type_uuid:
        type_uuid = str(uuid4())
    if not q_characteristics:
        q_characteristics = fixed_q_characteristics(cos_phi_rated)
    return pd.Series(
        {
            "id": id,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "node": node,
            "q_characteristics": q_characteristics,
            "type_uuid": type_uuid,
            "type_id": type_id,
            "capex": capex,
            "opex": opex,
            "s_rated": s_rated,
            "cos_phi_rated": cos_phi_rated,
            "e_storage": e_storage,
            "e_cons": e_cons,
        }
    ).rename(uuid)


def create_ev_charging_stations(data_dict):
    return EvChargingStations(create_data(data_dict, create_ev_charging_stations_data))


def create_ev_charging_stations_data(
    id,
    node,
    location_type,
    s_rated,
    v2g_support=False,
    charging_points=1,
    electric_current_type=ElectricCurrentType.AC,
    cos_phi=0.9,
    type_id=None,
    q_characteristics=None,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
):
    if not uuid:
        uuid = str(uuid4())
    if not q_characteristics:
        q_characteristics = fixed_q_characteristics(cos_phi)
    if not type_id:
        type_id = id
    type = evcs.evcs_type.substitute(
        id=id, s_rated=s_rated, current_type=electric_current_type.value
    )
    return pd.Series(
        {
            "id": id,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "node": node,
            "q_characteristics": q_characteristics,
            "cos_phi_rated": cos_phi,
            "charging_points": charging_points,
            "location_type": location_type,
            "type": type,
            "v2g_support": v2g_support,
        }
    ).rename(uuid)


def create_heat_pumps_data(
    id,
    node,
    thermal_bus,
    s_rated,
    p_thermal=None,
    q_characteristics=None,
    type_uuid=None,
    type_id=None,
    capex=0,
    opex=0,
    cos_phi_rated=0.9,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
):
    if not p_thermal:
        p_thermal = s_rated * 3
    if not q_characteristics:
        q_characteristics = fixed_q_characteristics(cos_phi_rated)
    if not type_uuid:
        type_uuid = str(uuid4())
    if not type_id:
        type_id = f"Type_{id}"
    if not uuid:
        uuid = str(uuid4())
    return pd.Series(
        {
            "id": id,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "node": node,
            "q_characteristics": q_characteristics,
            "thermal_bus": thermal_bus,
            "type_uuid": type_uuid,
            "type_id": type_id,
            "capex": capex,
            "opex": opex,
            "s_rated": s_rated,
            "cos_phi_rated": cos_phi_rated,
            "p_thermal": p_thermal,
        }
    ).rename(uuid)


def create_heat_pumps(data_dict):
    return HeatPumps(create_data(data_dict, create_heat_pumps_data))


def create_loads_data(
    id,
    node,
    s_rated,
    e_cons_annual,
    load_profile,
    dsm=True,
    q_characteristics=None,
    cos_phi_rated=0.9,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
):
    if not uuid:
        uuid = str(uuid4())
    if not q_characteristics:
        q_characteristics = fixed_q_characteristics(cos_phi_rated)
    return pd.Series(
        {
            "id": id,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "node": node,
            "q_characteristics": q_characteristics,
            "load_profile": load_profile,
            "dsm": dsm,
            "e_cons_annual": e_cons_annual,
            "s_rated": s_rated,
            "cos_phi_rated": cos_phi_rated,
        }
    ).rename(uuid)


def create_loads(data_dict):
    return Loads(create_data(data_dict, create_loads_data))


def create_energy_management_systems_data(
    id,
    node,
    connected_assets,
    control_strategy,
    q_characteristics=None,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
):
    if not uuid:
        uuid = str(uuid4())
    if not q_characteristics:
        q_characteristics = fixed_q_characteristics(0.9)
    return pd.Series(
        {
            "id": id,
            "node": node,
            "connected_assets": connected_assets,
            "control_strategy": control_strategy,
            "q_characteristics": q_characteristics,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
        }
    ).rename(uuid)


def create_energy_management_systems(data_dict):
    return EnergyManagementSystems(
        create_data(data_dict, create_energy_management_systems_data)
    )
