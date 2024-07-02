from typing import Union

from pandas import DataFrame

from pypsdm.models.input.container import GridContainer, RawGridContainer
from pypsdm.models.gwr import GridWithResults


def get_nodes(grid: Union[GridContainer | RawGridContainer | GridWithResults], volt_lvl: float) -> list[str]:
    nodes: DataFrame = grid.nodes.data

    return nodes[nodes["v_rated"].values == volt_lvl].index.to_list()


def get_lines(grid: Union[GridContainer | RawGridContainer | GridWithResults], volt_lvl: float) -> list[str]:
    nodes = get_nodes(grid, volt_lvl)
    return grid.filter_by_nodes(nodes).lines.data.index.to_list()
