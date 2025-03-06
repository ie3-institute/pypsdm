# Thermal Bus
from uuid import uuid4

import pandas as pd

from pypsdm.models.input.create.utils import create_data
from pypsdm.models.input.thermal.bus import ThermalBus
from pypsdm.models.input.thermal.house import ThermalHouse


def create_thermal_bus_data(
    id,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
):
    if not uuid:
        uuid = str(uuid4())
    return pd.Series(
        {
            "id": id,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
        }
    ).rename(uuid)


def create_thermal_busses(data_dict):
    return ThermalBus(create_data(data_dict, create_thermal_bus_data))


def create_thermal_house_data(
    id,
    thermal_bus,
    eth_losses,
    eth_capa,
    target_temperature=20,
    upper_temperature_limit=22,
    lower_temperature_limit=18,
    housing_type="house",
    number_inhabitants=2.0,
    uuid=None,
    operates_from=None,
    operates_until=None,
    operator=None,
):
    if not uuid:
        uuid = str(uuid4())
    return pd.Series(
        {
            "id": id,
            "thermal_bus": thermal_bus,
            "operates_from": operates_from,
            "operates_until": operates_until,
            "operator": operator,
            "eth_losses": eth_losses,
            "eth_capa": eth_capa,
            "target_temperature": target_temperature,
            "upper_temperature_limit": upper_temperature_limit,
            "lower_temperature_limit": lower_temperature_limit,
            "housing_type": housing_type,
            "number_inhabitants": number_inhabitants,
        }
    ).rename(uuid)


def create_thermal_houses(data_dict):
    return ThermalHouse(create_data(data_dict, create_thermal_house_data))
