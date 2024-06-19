from os import listdir
from os.path import join

from definitions import ROOT_DIR
from pypsdm import GridContainer
from pypsdm import GridWithResults
from pypsdm.ma_thesis.highlight_utils import get_nodes, get_lines
from pypsdm.plots.common.utils import *
from pypsdm.plots.grid import grid_plot


def read_grid(grid_name: str,
              result_folder_name: str,
              result_name: str,
              grid_delimiter: str = ",",
              result_delimiter: str = ",",
              primary_data_delimiter: str = ",") -> GridWithResults:
    grid_path = join(get_base_path(), "grids", grid_name)
    result_path = join(get_base_path(), "results", result_folder_name, result_name, "rawOutputData")

    return GridWithResults.from_csv(
        grid_path=grid_path,
        result_path=result_path,
        grid_delimiter=grid_delimiter,
        result_delimiter=result_delimiter,
        primary_data_delimiter=primary_data_delimiter
    )


def get_base_path():
    return join(ROOT_DIR, "input", "ma_thesis")

def plot_with_highlights(grid: GridContainer):
    mv_20 = get_nodes(grid, 20.0)
    mv_10 = get_nodes(grid, 10.0)
    mv_30 = get_nodes(grid, 30.0)
    hv = get_nodes(grid, 110.0)

    mv_lines = get_lines(grid, 10.0) + get_lines(grid, 20.0) + get_lines(grid, 30.0)

    node_highlights = {
        RED: mv_10,
        ORANGE: mv_20,
        BROWN: mv_30,
        PURPLE: hv
    }

    line_highlights = {
        YELLOW: mv_lines
    }

    return grid_plot(grid, background="white-bg", node_highlights=node_highlights, line_highlights=line_highlights)


def get_plot(path: str,
             delimiter=",",
             primary_data_delimiter=","):
    gwr = GridContainer.from_csv(path, delimiter, primary_data_delimiter)

    return plot_with_highlights(gwr.grid)


def get_plots(path: str, delimiter=";", primary_data_delimiter=";"):
    files = [join(path, file) for file in listdir(path)]

    grids = list()

    for file in files:
        grids.append(get_plot(file, delimiter, primary_data_delimiter))

    return grids
