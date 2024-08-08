from pypsdm import RawGridContainer, Transformers2W


def find_slack_downstream(rg: RawGridContainer) -> str:
    """
    Find the downstream node of the slack node, which is the node on the transformer's
    lower voltage side.
    """
    slack_node = rg.nodes.get_slack_nodes()
    if len(slack_node.data) != 1:
        raise ValueError("Currently only implemented for singular slack nodes.")
    transformers = rg.transformers_2_w
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
