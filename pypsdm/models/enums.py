from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Type, TypeVar

if TYPE_CHECKING:
    from pypsdm.models.result.participant.dict import EntitiesResultDictMixin
    from pypsdm.models.ts.base import TimeSeries


class EntitiesEnum(Enum):
    def has_type(self):
        if self in {
            RawGridElementsEnum.LINE,
            RawGridElementsEnum.TRANSFORMER_2_W,
            RawGridElementsEnum.TRANSFROMER_3_W,
            SystemParticipantsEnum.ELECTRIC_VEHICLE,
            SystemParticipantsEnum.BIOMASS_PLANT,
            SystemParticipantsEnum.WIND_ENERGY_CONVERTER,
            SystemParticipantsEnum.STORAGE,
            SystemParticipantsEnum.HEAT_PUMP,
        }:
            return True
        else:
            return False

    def get_csv_input_file_name(self):
        return self.value + "_input.csv"

    def get_csv_result_file_name(self):
        return self.value + "_res.csv"

    def get_type_file_name(self):
        assert self.has_type() is True
        return self.value + "_type_input.csv"

    def get_plot_name(self):
        return self.value.replace("_", " ").title()

    def get_result_type(self) -> type[TimeSeries]:
        # locally to avoid circular imports
        from pypsdm.models.result.grid.connector import ConnectorCurrent
        from pypsdm.models.result.grid.switch import SwitchResult
        from pypsdm.models.result.grid.transformer import Transformer2WResult
        from pypsdm.models.ts.types import (
            ComplexPower,
            ComplexPowerWithSoc,
            ComplexVoltage,
        )

        if isinstance(self, SystemParticipantsEnum):
            if self.has_soc():
                return ComplexPowerWithSoc
            else:
                return ComplexPower
        elif isinstance(self, RawGridElementsEnum):
            match self:
                case RawGridElementsEnum.NODE:
                    return ComplexVoltage
                case RawGridElementsEnum.TRANSFORMER_2_W:
                    return Transformer2WResult
                case RawGridElementsEnum.LINE:
                    return ConnectorCurrent
                case RawGridElementsEnum.SWITCH:
                    return SwitchResult
                case _:
                    raise NotImplementedError(
                        f"Result type {self} not implemented yet!"
                    )
        else:
            raise ValueError(f"Entity type {self} not supported!")

    def get_result_dict_type(self) -> Type["EntitiesResultDictMixin"]:
        from pypsdm.models.result.grid.line import LinesResult
        from pypsdm.models.result.grid.node import NodesResult
        from pypsdm.models.result.grid.switch import SwitchesResult
        from pypsdm.models.result.grid.transformer import Transformers2WResult
        from pypsdm.models.result.participant.dict import (
            EmsResult,
            EvcsResult,
            EvsResult,
            FixedFeedInsResult,
            HpsResult,
            LoadsResult,
            PvsResult,
            StoragesResult,
            WecsResult,
        )
        from pypsdm.models.result.participant.flex_options import FlexOptionsDict

        match self:
            case RawGridElementsEnum.NODE:
                return NodesResult
            case RawGridElementsEnum.LINE:
                return LinesResult
            case RawGridElementsEnum.TRANSFORMER_2_W:
                return Transformers2WResult
            case RawGridElementsEnum.SWITCH:
                return SwitchesResult
            case SystemParticipantsEnum.ELECTRIC_VEHICLE:
                return EvsResult
            case SystemParticipantsEnum.EV_CHARGING_STATION:
                return EvcsResult
            case SystemParticipantsEnum.FIXED_FEED_IN:
                return FixedFeedInsResult
            case SystemParticipantsEnum.LOAD:
                return LoadsResult
            case SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT:
                return PvsResult
            case SystemParticipantsEnum.WIND_ENERGY_CONVERTER:
                return WecsResult
            case SystemParticipantsEnum.STORAGE:
                return StoragesResult
            case SystemParticipantsEnum.ENERGY_MANAGEMENT:
                return EmsResult
            case SystemParticipantsEnum.HEAT_PUMP:
                return HpsResult
            case SystemParticipantsEnum.FLEX_OPTIONS:
                return FlexOptionsDict
            case sp:
                raise NotImplementedError(f"No result dict type for {sp}")


EntityEnumType = TypeVar("EntityEnumType", bound=EntitiesEnum)


class SystemParticipantsEnum(EntitiesEnum):
    BIOMASS_PLANT = "bm"
    COMBINED_HEAT_AND_POWER = "chp"
    ELECTRIC_VEHICLE = "ev"
    EV_CHARGING_STATION = "evcs"
    FIXED_FEED_IN = "fixed_feed_in"
    LOAD = "load"
    PHOTOVOLTAIC_POWER_PLANT = "pv"
    WIND_ENERGY_CONVERTER = "wec"
    STORAGE = "storage"
    ENERGY_MANAGEMENT = "em"
    HEAT_PUMP = "hp"
    FLEX_OPTIONS = "flex_options"
    PRIMARY_DATA = "primary_data"
    PARTICIPANTS_SUM = "participants_sum"

    @staticmethod
    def values():
        return [participant for participant in EntitiesEnum]

    def has_soc(self):
        return self in {
            SystemParticipantsEnum.ELECTRIC_VEHICLE,
            SystemParticipantsEnum.STORAGE,
        }


class RawGridElementsEnum(EntitiesEnum):
    NODE = "node"
    LINE = "line"
    TRANSFORMER_2_W = "transformer_2_w"
    TRANSFROMER_3_W = "transformer_3_w"
    SWITCH = "switch"
    MEASUREMENT_UNIT = "measurement_unit"


class ThermalGridElementsEnum(EntitiesEnum):
    THERMAL_BUS = "thermal_bus"
    THERMAL_GRID = "thermal_grid"
    THERMAL_HOUSE = "thermal_house"

class MappingEnum(EntitiesEnum):
    ExtEntity = "ext_entity"

    def get_csv_input_file_name(self):
        return f"{self.value}_mapping.csv"

class TimeSeriesEnum(EntitiesEnum):
    P_TIME_SERIES = "its_p"
    PQ_TIME_SERIES = "its_pq"
    PQH_TIME_SERIES = "its_pqh"  # pq time series with heat demand

    def get_csv_input_file_name(self, uuid: str):
        return f"{self.value}_{uuid}.csv"

    def get_csv_result_file_name(self):
        raise NotImplementedError("Time series are by definition input data!")

    def get_type_file_name(self):
        raise NotImplementedError("Types for time series do not exist!")

    def get_plot_name(self):
        return self.value

    def get_result_type(self):
        raise NotImplementedError("Result type defined for time series!")


class ElectricCurrentType(Enum):
    AC = "AC"
    DC = "DC"
