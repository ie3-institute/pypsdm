from pandas import DataFrame

from pypsdm import GridResultContainer, GridContainer, GridWithResults

class SubGrid:
    nr: int
    name: str
    grid: GridContainer

    def __init__(self, nr: int, name: str, grid: GridContainer):
        self.nr = nr
        self.name = name
        self.grid = grid

    def transformers(self) -> list[str]:
        return self.grid.transformers_2_w.data.index.to_list()

    @classmethod
    def build(cls, grid: GridContainer) -> dict[int, "SubGrid"]:
        from pypsdm.ma_thesis.utils import split_into_subgrids, get_subgrid_to_names, sort

        subgrids = split_into_subgrids(grid)
        names = get_subgrid_to_names(grid)

        return sort(
            {subgrid: SubGrid(subgrid, names[subgrid], subgrids[subgrid]) for subgrid in subgrids.keys()})


class SubGridInfo:
    sub_grid: SubGrid
    node_res: DataFrame
    node_min_max: DataFrame
    line_utilisation: DataFrame

    def __init__(self, sub_grid: SubGrid, results: GridResultContainer):
        from pypsdm.ma_thesis.analyse import analyse_nodes, analyse_lines

        self.sub_grid = sub_grid
        self.node_res, self.node_min_max = analyse_nodes(sub_grid.name, sub_grid.grid, results.nodes)
        self.line_utilisation = analyse_lines(sub_grid.grid, results.lines)

    def get_transformers(self) -> list[str]:
        return self.sub_grid.grid.transformers_2_w.data.index.to_list()

    @classmethod
    def build(cls, gwr: GridWithResults) -> dict[int, "SubGridInfo"]:
        from pypsdm.ma_thesis.utils import sort

        sub_grids = SubGrid.build(gwr.grid)
        return sort({subgrid: cls(sub_grids[subgrid], gwr.results) for subgrid in sub_grids.keys()})
