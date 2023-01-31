from dataclasses import dataclass

from pandas import DataFrame

from psdm_analysis.io.utils import read_csv
from psdm_analysis.models.entity import Entities


@dataclass(frozen=True)
class Transformers2W(Entities):
    data: DataFrame

    @classmethod
    def from_csv(cls, path: str, delimiter: str):
        return cls(read_csv(path, "transformer_2_w_input.csv", delimiter))
