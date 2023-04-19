from dataclasses import dataclass

import plotly.express as px

from psdm_analysis.models.result.grid.enhanced_node import EnhancedNodesResult
from psdm_analysis.models.result.grid.node import NodesResult


@dataclass(frozen=True)
class NodesResultPlotter:
    results: NodesResult

    def boxplot_v_mag(self, uuid: str):
        node_res = self.results.entities.get(uuid)
        return px.box(node_res.v_mag)

    def boxplots_v_mag(self):
        return px.box(self.results.v_mag)

    def boxplot_v_ang(self, uuid: str):
        node_res = self.results.entities.get(uuid)
        return px.box(node_res.v_ang)

    def boxplots_v_ang(self):
        return px.box(self.results.v_ang)

    def lineplots_v_mag(self):
        return px.line(self.results.v_mag)

    def lineplots_v_ang(self):
        return px.line(self.results.v_ang)


@dataclass(frozen=True)
class EnhancedNodesResultPlotter(NodesResultPlotter):
    results: EnhancedNodesResult

    def lineplots_p(self):
        return px.line(self.results.p)

    def boxplots_p(self):
        return px.box(self.results.p)
