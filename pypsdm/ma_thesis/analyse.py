import pandas as pd
from pandas import DataFrame

from pypsdm import GridContainer, NodesResult, LinesResult, GridWithResults


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


def analyse_lines(name, grid: GridContainer, results: LinesResult) -> (DataFrame, DataFrame):
    uuids = grid.lines.data.index.to_list()
    line_res = results.subset(uuids).utilisation(grid.lines)
    line_max = line_res.max(axis=1).to_frame(name)

    return line_res, line_max


def analyse_transformers2w(uuids: list[str], gwr: GridWithResults) -> DataFrame:
    df = gwr.transformers_2_w.data

    def uuid_to_id(uuid: str):
        return df[df.index.values == uuid]["id"].to_list()[0]

    transformer2w_res = pd.concat(
        {uuid_to_id(uuid): gwr.transformers_2_w_res[uuid].utilisation(uuid, gwr, "lv") for uuid in uuids},
        axis=1
    )

    return transformer2w_res
