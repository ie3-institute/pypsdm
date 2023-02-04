import re
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class CurrentType(Enum):
    AC = "ac"
    DC = "dc"


@dataclass(frozen=True)
class ChargingPointType:
    type_id: str
    # in kW
    power: float
    current_type: CurrentType
    synonymous_ids: set[str]


HOUSEHOLD_SOCKET = ChargingPointType(
    "HouseholdSocket", 2.3, CurrentType.AC, {"household", "hhs", "schuko-simple"}
)

BLUE_HOUSEHOLD_SOCKET = ChargingPointType(
    "BlueHouseholdSocket",
    3.6,
    CurrentType.AC,
    {"bluehousehold", "bhs", "schuko-camping"},
)

CEE16A_SOCKET = ChargingPointType("Cee16ASocket", 11, CurrentType.AC, {"cee16"})

CEE32A_SOCKET = ChargingPointType("Cee32ASocket", 22, CurrentType.AC, {"cee32"})

CEE63A_SOCKET = ChargingPointType("Cee63ASocket", 43, CurrentType.AC, {"cee63"})

CHARGING_STATION_TYPE_1 = ChargingPointType(
    "ChargingStationType1", 7.2, CurrentType.AC, {"cst1", "stationtype1", "cstype1"}
)

CHARGING_STATION_TYPE_2 = ChargingPointType(
    "ChargingStationType2", 43, CurrentType.AC, {"cst2", "stationtype2", "cstype2"}
)

CHARGING_STATION_CCS_COMBO_TYPE_1 = ChargingPointType(
    "ChargingStationCcsComboType1", 11, CurrentType.DC, {"csccs1", "csccscombo1"}
)

CHARGING_STATION_CCS_COMBO_TYPE_2 = ChargingPointType(
    "ChargingStationCcsComboType2", 50, CurrentType.DC, {"csccs2", "csccscombo2"}
)

TESLA_SUPER_CHARGER_V1 = ChargingPointType(
    "TeslaSuperChargerV1",
    135,
    CurrentType.DC,
    {"tesla1", "teslav1", "supercharger1", "supercharger"},
)

TESLA_SUPER_CHARGER_V2 = ChargingPointType(
    "TeslaSuperChargerV2",
    150,
    CurrentType.DC,
    {"tesla2", "teslav2", "supercharger2", "supercharger2"},
)

TESLA_SUPER_CHARGER_V3 = ChargingPointType(
    "TeslaSuperChargerV3",
    250,
    CurrentType.DC,
    {"tesla3", "teslav3", "supercharger3", "supercharger3"},
)

common_charging_point_types = [
    HOUSEHOLD_SOCKET,
    BLUE_HOUSEHOLD_SOCKET,
    CEE16A_SOCKET,
    CEE32A_SOCKET,
    CEE63A_SOCKET,
    CHARGING_STATION_TYPE_1,
    CHARGING_STATION_TYPE_2,
    CHARGING_STATION_CCS_COMBO_TYPE_1,
    CHARGING_STATION_CCS_COMBO_TYPE_2,
    TESLA_SUPER_CHARGER_V1,
    TESLA_SUPER_CHARGER_V2,
    TESLA_SUPER_CHARGER_V3,
]


def get_common_charging_point_type(id: str):
    for charging_point_type in common_charging_point_types:
        if (
            id == charging_point_type.type_id
            or id in charging_point_type.synonymous_ids
        ):
            return charging_point_type
    return


def parse_evcs_type(type_str: str) -> ChargingPointType:

    common_type = get_common_charging_point_type(type_str)
    if common_type:
        return common_type

    regex = "\(.*\)$"
    match = re.search(regex, type_str)
    if match:
        power, current_type = match.group().strip("()").split("|")
        current_type = CurrentType[current_type]
        return ChargingPointType(type_str, power, current_type, set())
    else:
        raise ValueError(f"Can not determine power of {type_str}!")


def parse_evcs_type_info(type_str: str):
    evcs_type = parse_evcs_type(type_str)
    return pd.Series(evcs_type.__dict__)
