from enum import Enum
from typing import TypeVar


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

    def get_result_type(self):
        # locally to avoid circular imports
        from psdm_analysis.models.result.grid.connector import ConnectorResult
        from psdm_analysis.models.result.grid.node import NodeResult
        from psdm_analysis.models.result.grid.transformer import Transformer2WResult
        from psdm_analysis.models.result.power import PQResult, PQWithSocResult

        if isinstance(self, SystemParticipantsEnum):
            if self.has_soc():
                return PQWithSocResult
            else:
                return PQResult
        elif isinstance(self, RawGridElementsEnum):
            match self:
                case RawGridElementsEnum.NODE:
                    return NodeResult
                case RawGridElementsEnum.TRANSFORMER_2_W:
                    return Transformer2WResult
                case RawGridElementsEnum.LINE:
                    return ConnectorResult
                case _:
                    raise NotImplementedError(
                        f"Result type {self} not implemented yet!"
                    )
        else:
            raise ValueError(f"Entity type {self} not supported!")


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
        return [participant for participant in SystemParticipantsEnum]

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
