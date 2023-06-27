from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Union

from networkx import Graph

from psdm_analysis.models.input.connector.lines import Lines
from psdm_analysis.models.input.connector.switches import Switches
from psdm_analysis.models.input.connector.transformer import Transformers2W
from psdm_analysis.models.input.container.mixins import ContainerMixin
from psdm_analysis.models.input.container.participants_container import (
    SystemParticipantsContainer,
)
from psdm_analysis.models.input.entity import Entities
from psdm_analysis.models.input.node import Nodes
from psdm_analysis.models.primary_data import PrimaryData
from psdm_analysis.models.result.power import PQResult


@dataclass(frozen=True)
class RawGridContainer(ContainerMixin):
    nodes: Nodes
    lines: Lines
    transformers_2_w: Transformers2W
    switches: Switches

    def to_list(self, include_empty: bool = False) -> list[Entities]:
        grid_elements = [self.nodes, self.lines, self.transformers_2_w, self.switches]
        return grid_elements if include_empty else [e for e in grid_elements if e]

    def get_branches(self, as_graphs=False) -> Union[list[list[str]], list[Graph]]:
        """
        Returns all branches, branching off from the slack node of the grid.
        The branches are either returned as a list of lists, where each list contains the node uuids of the branch,
        starting at the slack node, or rather as subgraphs containing all nodes and edges of the branch.

        Currently only works for single slack node and single voltage level grids.

        Args:
            as_graphs: If True, returns the branches as subgraphs, otherwise as lists of node uuids.

        Returns:
            A list of lists or a list of subgraphs, containing the branches of the grid.
        """

        slack_node = self.nodes.get_slack_nodes()
        if len(slack_node.data) != 1:
            raise ValueError("Currently only implemented for singular slack nodes.")
        transformers = self.transformers_2_w
        slack_transformers = Transformers2W(
            transformers.data[
                (transformers.node_a.isin(slack_node.uuid.to_list()))
                | (transformers.node_b.isin(slack_node.uuid.to_list()))
            ]
        )
        slack_connected_node = (
            set(slack_transformers.node_a)
            .union(slack_transformers.node_b)
            .difference(slack_node.uuid)
        )
        if len(slack_connected_node) > 1:
            raise ValueError(
                "There are multiple nodes connected to the slack node via a transformer."
            )
        elif len(slack_connected_node) == 0:
            raise ValueError("Did not find a slack node!")
        slack_connected_node = slack_connected_node.pop()
        graph = self.build_networkx_graph()
        branches = self._find_branches(graph, slack_connected_node)
        branches = [[slack_connected_node] + branch for branch in branches]
        if as_graphs:
            return [graph.subgraph(branch).copy() for branch in branches]
        return branches

    def build_networkx_graph(self, include_transformer: bool = False) -> Graph:
        graph = Graph()
        closed_switches = self.switches.get_closed()
        line_data_dicts = self.lines.data.apply(
            lambda row: {"length": row["length"]}, axis=1
        )

        graph.add_nodes_from(self.nodes.uuid)
        graph.add_edges_from(zip(self.lines.node_a, self.lines.node_b, line_data_dicts))
        graph.add_edges_from(zip(closed_switches.node_a, closed_switches.node_b))
        if include_transformer:
            graph.add_edges_from(
                zip(self.transformers_2_w.node_a, self.transformers_2_w.node_b)
            )
        return graph

    @staticmethod
    def _find_branches(G: Graph, start_node):
        visited = set()
        visited.add(start_node)
        branches = []

        def dfs(node, path):
            visited.add(node)
            path.append(node)

            for neighbor in G.neighbors(node):
                if neighbor not in visited:
                    dfs(neighbor, path)

        for neighbor in G.neighbors(start_node):
            if neighbor not in visited:
                path = []
                dfs(neighbor, path)
                branches.append(path)

        return branches

    @classmethod
    def from_csv(cls, path: str, delimiter: str) -> "RawGridContainer":
        nodes = Nodes.from_csv(path, delimiter)
        lines = Lines.from_csv(path, delimiter)
        transformers_2_w = Transformers2W.from_csv(path, delimiter)
        switches = Switches.from_csv(path, delimiter)
        return cls(
            nodes=nodes,
            lines=lines,
            transformers_2_w=transformers_2_w,
            switches=switches,
        )


@dataclass(frozen=True)
class GridContainer(ContainerMixin):
    raw_grid: RawGridContainer
    # todo: we keep the participant containers effectively twice with the mapping
    participants: SystemParticipantsContainer
    primary_data: PrimaryData
    node_participants_map: Dict[str, SystemParticipantsContainer]

    def to_list(self, include_empty: bool = False, include_primary_data: bool = False):
        grid = [self.raw_grid, self.participants]
        return grid if not include_primary_data else grid + [self.primary_data]

    def get_nodal_primary_data(self):
        time_series = []
        nodal_primary_data = dict()
        for node, participants_container in self.node_participants_map.items():
            participants_uuids = participants_container.uuids().tolist()
            node_primary_data = self.primary_data.get_for_participants(
                participants_uuids
            )
            time_series.extend(node_primary_data)
            node_primary_data_agg = PQResult.sum(node_primary_data)
            nodal_primary_data[node] = node_primary_data_agg
        return nodal_primary_data

    def get_nodal_sp_count_and_power(self):
        data = {}
        for node_uuid, sps in self.node_participants_map.items():
            nodal_data = {}
            for sp in sps.to_list(include_empty=False):
                sp_id = sp.get_enum().value
                count = len(sp.data)
                data_str = f"Count: {count}"
                # check if sp has a property named s_rated
                if hasattr(sp, "s_rated"):
                    s_rated = round(sp.s_rated.sum(), 2)
                    data_str += f", Rated Power: {s_rated} kw"
                nodal_data[sp_id] = data_str
            data[node_uuid] = nodal_data
        return data

    def filter_by_date_time(self, time: Union[datetime, list[datetime]]):
        return GridContainer(
            raw_grid=self.raw_grid,
            participants=self.participants,
            primary_data=self.primary_data.filter_by_date_time(time),
            node_participants_map=self.node_participants_map,
        )

    def to_csv(
        self,
        path: str,
        include_primary_data: bool,
        mkdirs: bool = True,
        delimiter: str = ",",
    ):
        for container in self.to_list(include_primary_data=include_primary_data):
            try:
                container.to_csv(path, mkdirs=mkdirs, delimiter=delimiter)
            except Exception as e:
                raise IOError(f"Could not write {container} to {path}.", e)

    @classmethod
    def from_csv(cls, path: str, delimiter: str, primary_data_delimiter: str = None):
        if not primary_data_delimiter:
            primary_data_delimiter = delimiter
        raw_grid = RawGridContainer.from_csv(path, delimiter)
        participants = SystemParticipantsContainer.from_csv(path, delimiter)
        node_participants_map = participants.build_node_participants_map(raw_grid.nodes)
        primary_data = PrimaryData.from_csv(path, primary_data_delimiter)
        return cls(raw_grid, participants, primary_data, node_participants_map)
