from pandas import Series

from pypsdm import GridContainer, GridWithResults


def get_nodes_to_subnet(grid: GridContainer) -> dict[int, list[str]]:
    nodes = grid.nodes
    subnets = nodes.subnet.drop_duplicates().to_list()
    return {subnet: nodes[nodes.subnet.values == subnet].index.to_list() for subnet in subnets}


def get_subnet_to_names(grid: GridContainer) -> dict[int, str]:
    nodes = grid.nodes
    nodes_to_subnet = get_nodes_to_subnet(grid)
    return {subnet: nodes[nodes_to_subnet[subnet][0]].id.split(" Bus")[0] for subnet in nodes_to_subnet.keys()}


def split_into_subnets(grid: GridContainer) -> dict[int, GridContainer]:
    nodes_to_subnet = get_nodes_to_subnet(grid)
    return {subnet: grid.filter_by_nodes(nodes) for subnet, nodes in nodes_to_subnet.items()}


def get_trafo_2w_info(gwr: GridWithResults) -> dict[str, Series]:
    transformers = gwr.transformers_2_w
    return {uuid: transformers[uuid] for uuid in transformers.data.index.to_list()}


def sort(dictionary: dict):
    return dict(sorted(dictionary.items()))
