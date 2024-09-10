from dataclasses import dataclass
from pathlib import Path
from typing import Union

from networkx import Graph

from pypsdm.graph import find_branches
from pypsdm.models.enums import RawGridElementsEnum
from pypsdm.models.input.connector.lines import Lines
from pypsdm.models.input.connector.switches import Switches
from pypsdm.models.input.connector.transformer import Transformers2W
from pypsdm.models.input.container.mixins import ContainerMixin
from pypsdm.models.input.entity import Entities
from pypsdm.models.input.node import Nodes


@dataclass(frozen=True)
class RawGridContainer(ContainerMixin):
    nodes: Nodes
    lines: Lines
    transformers_2_w: Transformers2W
    switches: Switches

    def __eq__(self, other):
        return super().__eq__(other)

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
        branches = find_branches(graph, slack_connected_node)
        branches = [[slack_connected_node] + branch for branch in branches]
        if as_graphs:
            return [graph.subgraph(branch).copy() for branch in branches]
        return branches

    def get_with_enum(self, enum: RawGridElementsEnum):
        match enum:
            case RawGridElementsEnum.NODE:
                return self.nodes
            case RawGridElementsEnum.LINE:
                return self.lines
            case RawGridElementsEnum.TRANSFORMER_2_W:
                return self.transformers_2_w
            case RawGridElementsEnum.SWITCH:
                return self.switches
            case _:
                raise ValueError(f"Unknown enum {enum}")

    def build_networkx_graph(self, include_transformer: bool = False) -> Graph:
        graph = Graph()
        closed_switches = self.switches.get_closed()
        line_data_dicts = self.lines.data.apply(
            lambda row: {"weight": row["length"]}, axis=1
        )

        graph.add_nodes_from(self.nodes.uuid)
        graph.add_edges_from(zip(self.lines.node_a, self.lines.node_b, line_data_dicts))
        graph.add_edges_from(zip(closed_switches.node_a, closed_switches.node_b))
        if include_transformer:
            graph.add_edges_from(
                zip(self.transformers_2_w.node_a, self.transformers_2_w.node_b)
            )
        return graph

    def filter_by_nodes(self, nodes: Union[str, list[str], set[str]]):
        return RawGridContainer(
            self.nodes.filter_by_nodes(nodes),
            self.lines.filter_by_nodes(nodes, both_in_nodes=True),
            self.transformers_2_w.filter_by_nodes(nodes, both_in_nodes=False),
            self.switches.filter_by_nodes(nodes, both_in_nodes=True),
        )

    def admittance_matrix(self, uuid_to_idx: dict):
        """TODO: `parallelDevices` not yet considered."""
        lines_admittance = self.lines.admittance_matrix(uuid_to_idx)
        transformers_admittance = self.transformers_2_w.admittance_matrix(uuid_to_idx)
        return lines_admittance + transformers_admittance

    def find_slack_downstream(self) -> str:
        """
        Find the downstream node of the slack node, which is the node on the transformer's
        lower voltage side.
        """
        from pypsdm import Transformers2W

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
        return slack_connected_node.pop()

    @classmethod
    def from_csv(
        cls, path: str | Path, delimiter: str | None = None
    ) -> "RawGridContainer":
        nodes = Nodes.from_csv(path, delimiter)
        lines = Lines.from_csv(path, delimiter, must_exist=False)
        transformers_2_w = Transformers2W.from_csv(path, delimiter, must_exist=False)
        switches = Switches.from_csv(path, delimiter, must_exist=False)
        return cls(
            nodes=nodes,
            lines=lines,
            transformers_2_w=transformers_2_w,
            switches=switches,
        )

    @classmethod
    def empty(cls):
        return cls(
            nodes=Nodes.create_empty(),
            lines=Lines.create_empty(),
            transformers_2_w=Transformers2W.create_empty(),
            switches=Switches.create_empty(),
        )
