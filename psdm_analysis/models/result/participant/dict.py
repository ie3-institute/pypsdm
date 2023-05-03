import logging
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, TypeVar

from pandas.core.groupby import DataFrameGroupBy

from psdm_analysis.io.utils import check_filter, csv_to_grpd_df, get_file_path
from psdm_analysis.models.entity import ResultEntities
from psdm_analysis.models.input.enums import EntitiesEnum, EntityType

ResultDictType = TypeVar("ResultDictType", bound="ResultDict")


@dataclass(frozen=True)
class ResultDict(ABC):
    entity_type: EntitiesEnum
    entities: Dict[str, ResultEntities]

    def __len__(self):
        return len(self.entities)

    def __contains__(self, uuid):
        return uuid in self.entities

    def __getitem__(self, get):
        print(get)
        match get:
            case str():
                return self.entities[get]
            case slice():
                start, stop, step = get.start, get.stop, get.step
                if step is not None:
                    logging.warning("Step is not supported for slicing. Ignoring it.")
                if not (isinstance(start, datetime) and isinstance(stop, datetime)):
                    raise ValueError("Only datetime slicing is supported")
                entities = {
                    key: e.filter_for_time_interval(start, stop)
                    for key, e in self.entities.items()
                }
                return type(self)(self.entity_type, entities)
            case _:
                raise ValueError(
                    "Only get by uuid or datetime slice for filtering is supported."
                )

    @classmethod
    def from_csv(
        cls,
        entity_type: EntityType,
        simulation_data_path: str,
        delimiter: str,
        simulation_end: datetime,
        filter_start: Optional[datetime] = None,
        filter_end: Optional[datetime] = None,
    ) -> ResultDictType:
        check_filter(filter_start, filter_end)
        grpd_df = ResultDict.get_grpd_df(
            entity_type,
            simulation_data_path,
            delimiter,
        )
        if not grpd_df:
            logging.debug("There are no " + str(cls))
            return cls.create_empty(entity_type)
        entities = dict(
            grpd_df.apply(
                lambda grp: entity_type.get_result_type().build(
                    entity_type,
                    grp.name,
                    grp.drop(columns=["input_model"]),
                    simulation_end,
                )
            )
        )
        res = cls(
            entity_type,
            entities,
        )
        return (
            res
            if not filter_start
            else res.filter_for_time_interval(filter_start, filter_end)
        )

    @staticmethod
    def get_grpd_df(
        entity_type: EntityType,
        simulation_data_path: str,
        delimiter: str,
    ) -> Optional[DataFrameGroupBy]:
        file_name = entity_type.get_csv_result_file_name()
        path = get_file_path(simulation_data_path, file_name)

        if not path.exists():
            logging.info(
                "No results built for {} since {} does not exist".format(
                    file_name, str(path)
                )
            )
            return None

        return csv_to_grpd_df(file_name, simulation_data_path, delimiter)

    @staticmethod
    def safe_get_path(entity_type: EntityType, data_path: str) -> Optional[str]:
        file_name = entity_type.get_csv_result_file_name()
        path = get_file_path(data_path, file_name)
        if path.exists():
            return path
        else:
            logging.info(
                "No results built for {} since {} does not exist".format(
                    file_name, str(path)
                )
            )
            return None

    @classmethod
    def create_empty(cls, sp_type):
        return cls(sp_type, dict())

    def uuids(self):
        return list(self.entities.keys())

    def results(self):
        return list(self.entities.values())

    # noinspection PyArgumentList
    def subset(self, uuids):
        matched_participants = {
            uuid: self.entities[uuid] for uuid in self.entities.keys() & uuids
        }

        return type(self)(self.entity_type, matched_participants)

    def subset_split(self, uuids: [str]):
        """
        Returns a results result containing the given uuids and a results result containing the remaining uuids.
        :param uuids: the uuids with which to split the result
        :return:
        """

        rmd_uuids = self.entities.keys() - uuids
        return self.subset(uuids), self.subset(rmd_uuids)

    # noinspection PyArgumentList
    def filter_for_time_interval(self, start: datetime, end: datetime):
        return type(self)(
            self.entity_type,
            {
                uuid: result.filter_for_time_interval(start, end)
                for uuid, result in self.entities.items()
            },
        )
