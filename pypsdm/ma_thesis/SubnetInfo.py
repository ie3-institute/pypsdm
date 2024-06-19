import pandas as pd
from pandas import DataFrame

from pypsdm import GridResultContainer, NodesResult, LinesResult, GridContainer, GridWithResults
from pypsdm.ma_thesis.utils import split_into_subnets, get_subnet_to_names, sort


class SubnetInfo:
    nr: int
    name: str
    node_res: DataFrame
    node_min_max: DataFrame
    line_utilisation: DataFrame
    transformers: list[str]

    def __init__(self, nr: int, name: str, grid: GridContainer, results: GridResultContainer):
        self.nr = nr
        self.name = name
        self.transformers = grid.transformers_2_w.data.index.to_list()

        self.__analyse_nodes__(grid, results.nodes)
        self.__analyse_lines__(grid, results.lines)

    def __analyse_nodes__(self, grid: GridContainer, results: NodesResult):
        nodes = grid.nodes.data.index.to_list()
        results = {node: results[node].data["v_mag"] for node in nodes}
        self.node_res = pd.concat(results, axis=1)
        self.node_min_max = pd.concat({self.name + " (min)": self.node_res.min(axis=1),
                                       self.name + " (max)": self.node_res.max(axis=1)}, axis=1)

    def __analyse_lines__(self, grid: GridContainer, results: LinesResult):
        uuids = grid.lines.data.index.to_list()
        self.line_utilisation = results.subset(uuids).utilisation(grid.lines)

    @classmethod
    def build(cls, gwr: GridWithResults) -> dict[int, "SubnetInfo"]:
        subnets = split_into_subnets(gwr.grid)
        names = get_subnet_to_names(gwr.grid)

        return sort(
            {subnet: SubnetInfo(subnet, names[subnet], subnets[subnet], gwr.results) for subnet in subnets.keys()})


def get_subnet_with_version(subnet: int, subnets: dict[str, dict[int, SubnetInfo]]) -> dict[str, SubnetInfo]:
    return {name: info[subnet] for name, info in subnets.items()}
