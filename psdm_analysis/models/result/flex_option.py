from dataclasses import dataclass
from typing import List

from pandas import Series

from psdm_analysis.models.entity import ResultEntities
from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.result.power import PQResult
from psdm_analysis.processing.series import add_series, hourly_mean_resample


@dataclass(frozen=True)
class FlexOptionResult(ResultEntities):
    def __add__(self, other: "FlexOptionResult"):
        p_ref_sum = add_series(self.p_ref(), other.p_ref(), "p_ref")
        p_min_sum = add_series(self.p_min(), other.p_min(), "p_min")
        p_max_sum = add_series(self.p_max(), other.p_max(), "p_max")
        summed_data = p_ref_sum.to_frame().join([p_min_sum, p_max_sum])
        return FlexOptionResult(
            self.type,
            "FlexResult - Sum",
            "FlexResult - Sum",
            summed_data,
        )

    @staticmethod
    def attributes() -> List[str]:
        return ["p_max", "p_min", "p_ref"]

    def p_max(self):
        return self.data["p_max"]

    def p_min(self):
        return self.data["p_min"]

    def p_ref(self):
        return self.data["p_ref"]

    def p_max_as_pq(self, sp_type: SystemParticipantsEnum) -> PQResult:
        return self._p_to_pq_res(sp_type, self.p_max())

    def p_ref_as_pq(self, sp_type: SystemParticipantsEnum) -> PQResult:
        return self._p_to_pq_res(sp_type, self.p_ref())

    def p_min_as_pq(self, sp_type: SystemParticipantsEnum):
        return self._p_to_pq_res(sp_type, self.p_min())

    def _p_to_pq_res(
        self, sp_type: SystemParticipantsEnum, p_series: Series
    ) -> PQResult:
        data = p_series.rename("p").to_frame()
        data["q"] = 0
        return PQResult(sp_type, "flex-signal", "flex-signal", data)

    def hourly_resample(self):
        updated_data = self.data.apply(lambda x: hourly_mean_resample(x))
        return FlexOptionResult(self.type, self.name, self.input_model, updated_data)

    def add_series(self, series: Series) -> "FlexOptionResult":
        updated_data = self.data.apply(
            lambda p_flex: add_series(p_flex, series, p_flex.name), axis=0
        )
        return FlexOptionResult(self.type, self.name, self.input_model, updated_data)
