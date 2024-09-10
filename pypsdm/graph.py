from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx
from networkx import Graph

from pypsdm.models.input.utils import find_slack_downstream

if TYPE_CHECKING:
    from pypsdm import RawGridContainer


def find_branches(G: Graph, start_node):
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
            path = [start_node]
            dfs(neighbor, path)
            branches.append(path)

    return branches


def find_n_hop_closest_in_slack_direction(
    uuid: str, n: int, raw_grid: RawGridContainer, candidates: set[str] | None = None
):
    slack_ds = find_slack_downstream(raw_grid)
    G = raw_grid.build_networkx_graph()
    if candidates is None:
        candidates = set(raw_grid.nodes.uuid)
    # find djikstra shortest path between uuid and slck_ds
    path = nx.shortest_path(G, uuid, slack_ds)
    closest = find_n_hop_closest_candidates(n, G, uuid, candidates)
    closest = [n for n in closest if n in path]
    return closest


def find_n_hop_closest_candidates(n: int, G, uuid, candidates):
    """
    Find all nodes within candidates that are n candidate hops away from the given node.
    """
    closest = set([uuid])
    for _ in range(n):
        for node in closest:
            closest = closest.union(find_closest_candidates(G, node, candidates))
    return closest


def find_closest_candidates(G: nx.Graph, node: str, candidates: set[str]) -> list[str]:
    """
    Starting from the node, find the closest nodes in all directions, that are in the
    candidates set.

    Args:
        G: The graph to search in.
        node: The node for which to find the closest candidates.
        candidates: The set of nodes to search for.
    """
    # NOTE: This might be added to pypsdm
    res = []
    visited = set()

    def preorder_dfs(cur: str):
        if cur in visited:
            return
        visited.add(cur)
        if cur in candidates and cur != node:
            res.append(cur)
            return
        for n in G.neighbors(cur):
            preorder_dfs(n)

    preorder_dfs(node)
    return res
