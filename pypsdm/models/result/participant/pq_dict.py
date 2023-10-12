import os.path
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd
from pandas import DataFrame, Series

from pypsdm.errors import ComparisonError
from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.input.participant.participant import SystemParticipantsWithCapacity
from pypsdm.models.result.participant.dict import ResultDict
from pypsdm.models.result.power import PQResult, PQWithSocResult
from pypsdm.processing.dataframe import join_dataframes


@dataclass(frozen=True)
class PQResultDict(ResultDict):
    entities: Dict[str, PQResult]

    @property
    def p(self) -> DataFrame:
        if not self.entities.values():
            return pd.DataFrame()
        return (
            pd.DataFrame({p_uuid: res.p for p_uuid, res in self.entities.items()})
            .fillna(method="ffill")
            .sort_index()
        )

    @property
    def q(self) -> DataFrame:
        if not self.entities.values():
            return pd.DataFrame()
        return (
            pd.DataFrame({p_uuid: res.q for p_uuid, res in self.entities.items()})
            .fillna(method="ffill")
            .sort_index()
        )

    def p_sum(self) -> Series:
        if not self.entities:
            return Series(dtype=float)
        return self.p.fillna(method="ffill").sum(axis=1).rename("p_sum")

    def q_sum(self):
        if not self.entities:
            return Series(dtype=float)
        return self.q.fillna(method="ffill").sum(axis=1).rename("q_sum")

    def sum(self) -> PQResult:
        return PQResult.sum(list(self.entities.values()))

    def energy(self) -> float:
        # todo make concurrent
        sum = 0
        for participant in self.entities.values():
            sum += participant.energy()
        return sum

    def get(self, key: str) -> PQResult:
        return self.entities[key]

    def subset(self, uuids):
        return type(self)(
            self.entity_type,
            {uuid: self.entities[uuid] for uuid in self.entities.keys() & uuids},
        )

    def load_and_generation(self):
        return self.sum().load_and_generation()

    def compare(self, other):
        errors = []

        # Compare time series
        self_keys = set(self.entities.keys())
        other_keys = set(other.entities.keys())
        entity_differences = self_keys.symmetric_difference(other_keys)
        if entity_differences:
            errors.append(
                ComparisonError(
                    f"Differences in entity keys. Following keys not in both dicts: {entity_differences}"
                )
            )

        key_intersection = self_keys & other_keys
        for key in key_intersection:
            try:
                self.entities[key].compare(other.entities[key])
            except ComparisonError as e:
                errors.append(e)

        if errors:
            raise ComparisonError(
                f"Found Differences in {type(self)} comparison: ", differences=errors
            )

    def to_csv(self, path: str, resample_rate: Optional[str] = None):
        file_name = self.entity_type.get_csv_result_file_name()

        def resample(data: DataFrame, input_model: str):
            data = (
                data.resample("60s").ffill().resample(resample_rate).mean()
                if resample_rate
                else data
            )
            data["uuid"] = data.apply(lambda _: str(uuid.uuid4()), axis=1)
            data["input_model"] = input_model
            return data

        resampled = [
            resample(participant.data, input_model)
            for input_model, participant in self.entities.items()
        ]
        df = join_dataframes(resampled)
        df.to_csv(os.path.join(path, file_name))


@dataclass(frozen=True)
class PQWithSocResultDict(PQResultDict):
    entity_type: SystemParticipantsEnum
    entities: Dict[str, PQWithSocResult]

    def sum_with_soc(self, inputs: SystemParticipantsWithCapacity) -> PQWithSocResult:
        if not self.entities:
            return PQWithSocResult.create_empty(self.entity_type, "", "")
        capacity_participant = []
        for participant_uuid, res in self.entities.items():
            capacity = inputs.get(participant_uuid)[inputs.capacity_attribute()]
            capacity_participant.append((capacity, res))
        return PQWithSocResult.sum_with_soc(capacity_participant)
