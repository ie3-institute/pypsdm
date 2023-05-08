from abc import ABC
from dataclasses import dataclass

import pandas as pd

from psdm_analysis.models.entity import Entities


@dataclass(frozen=True)
class Connector(Entities, ABC):
    @property
    def node_a(self):
        return self.data["node_a"]

    @property
    def node_b(self):
        return self.data["node_b"]

    @property
    def parallel_devices(self):
        return self.data["parallel_devices"]

    def nodes(self):
        return pd.concat([self.node_a, self.node_b])
