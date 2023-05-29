from psdm_analysis.models.grid_with_results import GridWithResults


def test_raw_grid_container(gwr):
    raw_grid_container = gwr.grid.raw_grid
    assert len(raw_grid_container.lines) == 291
    assert len(raw_grid_container.nodes) == 299


def test_grid_container(gwr):
    grid_container = gwr.grid
    assert len(grid_container.raw_grid.lines) == 291
    assert len(grid_container.raw_grid.nodes) == 299
    assert len(grid_container.participants.loads) == 496


def test_build_networkx_graph(gwr: GridWithResults):
    G = gwr.grid.raw_grid.build_networkx_graph()

    # all nodes and lines present
    assert len(G.nodes) == len(gwr.grid.raw_grid.nodes)
    assert len(G.edges) == len(gwr.grid.raw_grid.lines) + len(
        gwr.grid.raw_grid.switches.get_closed()
    )

    # correct line length in data dict
    for _, line in gwr.grid.raw_grid.lines.data.iterrows():
        assert G.has_edge(line["node_a"], line["node_b"])
        assert G.edges[(line["node_a"], line["node_b"])]["length"] == line["length"]
