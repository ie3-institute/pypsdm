import pandas as pd

from pypsdm.models.input.container.raw_grid import RawGridContainer


def grid_structure_summary(grid: RawGridContainer):
    line_length_sum = grid.lines.aggregated_line_length()
    return """
    Grid Structure Summary:
    -----------------------
    {nr_2w_transformers} two-winding transformers
    {nr_nodes} nodes
    {nr_lines} lines
    {line_length_sum} km aggregated line length
    """.format(
        nr_2w_transformers=len(grid.transformers_2_w.data),
        nr_nodes=len(grid.nodes.data),
        nr_lines=len(grid.lines.data),
        line_length_sum=line_length_sum,
    )


def branching_index(grid: RawGridContainer):
    """
    Calculates the average amount of branches connected to the nodes of the grid.

    Args:
        grid: The grid to calculate the branching index for.

    Returns:
        The branching index of the grid.
    """
    # all connections to nodes
    connections = pd.concat((grid.lines.node_a, grid.lines.node_b))
    # TODO: add switch evaluation
    # group connections by node uuid and calculate their amount
    nodal_connections = connections.groupby(connections).apply(
        lambda node_grp: len(node_grp)
    )
    return nodal_connections.sum() / len(nodal_connections)
