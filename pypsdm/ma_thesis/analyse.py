import pandas as pd
from pandas import DataFrame

from pypsdm import GridContainer, NodesResult, LinesResult


def analyse_nodes(name, grid: GridContainer, results: NodesResult) -> (DataFrame, DataFrame):
    nodes = grid.nodes.data.index.to_list()
    results = {node: results[node].data["v_mag"] for node in nodes}
    node_res = pd.concat(results, axis=1)
    node_min_max = pd.concat({name + " (min)": node_res.min(axis=1), name + " (max)": node_res.max(axis=1)}, axis=1)

    return node_res, node_min_max


def get_max_voltages(grid: GridContainer, results: dict[str, NodesResult]) -> DataFrame:
    nodes = grid.nodes.data.index.to_list()

    def get_max(result: NodesResult):
        return pd.concat({node: result[node].data["v_mag"] for node in nodes}, axis=1).max(axis=1)

    scenario_results = {scenario: get_max(result) for scenario, result in results.items()}

    return pd.concat(scenario_results, axis=1)


def get_min_voltages(grid: GridContainer, results: dict[str, NodesResult]) -> DataFrame:
    nodes = grid.nodes.data.index.to_list()

    def get_min(result: NodesResult):
        return pd.concat({node: result[node].data["v_mag"] for node in nodes}, axis=1).min(axis=1)

    scenario_results = {scenario: get_min(result) for scenario, result in results.items()}

    return pd.concat(scenario_results, axis=1)


def analyse_lines(grid: GridContainer, results: LinesResult):
    uuids = grid.lines.data.index.to_list()
    return results.subset(uuids).utilisation(grid.lines)
