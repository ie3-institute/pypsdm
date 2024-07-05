from os.path import join

from pandas import Series, DataFrame, Timedelta

from definitions import ROOT_DIR
from pypsdm import GridContainer, GridWithResults, GridResultContainer
from pypsdm.ma_thesis.subgrid import SubGrid, SubGridInfo


def get_base_path():
    return join(ROOT_DIR, "input", "ma_thesis")


def plot_output_folder():
    return join(get_base_path(), "plots")


def get_output_path(result_base_name: str, filename: str):
    return join(get_base_path(), "plots", result_base_name, filename)


def get_result(result_folder_name, result_name, delimiter: str = ",") -> str:
    path = join(get_base_path(), "results", result_folder_name, result_name, "rawOutputData")
    return GridResultContainer.from_csv(path, delimiter=delimiter)


def read_scenarios(
        grid_name: str,
        result_folder_name: str,
        result_base_name: str,
        result_suffix: str,
        grid_delimiter: str = ",",
        result_delimiter: str = ",",
) -> (GridContainer, dict[str, GridResultContainer]):
    grid_path = join(get_base_path(), "grids", grid_name)
    grid = GridContainer.from_csv(path=grid_path, delimiter=grid_delimiter)
    
    result_names = [result_base_name + "-" + str(nr) + "-" + result_suffix for nr in range(0, 3, 1)]
    results = {result_name: get_result(result_folder_name, result_name, result_delimiter) for result_name in
               result_names}

    return grid, results


def get_nodes_to_subgrid(grid: GridContainer) -> dict[int, list[str]]:
    nodes = grid.nodes
    subnets = nodes.subnet.drop_duplicates().to_list()
    return {subnet: nodes[nodes.subnet.values == subnet].index.to_list() for subnet in subnets}


def get_subgrid_to_names(grid: GridContainer) -> dict[int, str]:
    nodes = grid.nodes
    nodes_to_subnet = get_nodes_to_subgrid(grid)
    return {subnet: nodes[nodes_to_subnet[subnet][0]].id.split(" Bus")[0] for subnet in nodes_to_subnet.keys()}


def split_into_subgrids(grid: GridContainer) -> dict[int, GridContainer]:
    nodes_to_subnet = get_nodes_to_subgrid(grid)
    return {subnet: grid.filter_by_nodes(nodes) for subnet, nodes in nodes_to_subnet.items()}


def get_trafo_2w_info(gwr: GridWithResults) -> dict[str, Series]:
    transformers = gwr.transformers_2_w
    return {uuid: transformers[uuid] for uuid in transformers.data.index.to_list()}


def get_transformers_between(subgrid1: SubGrid, subgrid2: SubGrid):
    return list(set(subgrid1.transformers()).intersection(subgrid2.transformers()))


def get_subgrid_with_version(subgrid: int, subgrids: dict[str, dict[int, SubGridInfo]]) -> dict[str, SubGridInfo]:
    return {name: info[subgrid] for name, info in subgrids.items()}


def sort(dictionary: dict):
    return dict(sorted(dictionary.items()))


def hours_index(df: DataFrame):
    copy = df.copy()
    new_index = [str(i) for i, _ in enumerate(copy.index.to_list())]

    copy.index = new_index
    return copy

