def test_raw_grid_container(gwr):
    raw_grid_container = gwr.grid.raw_grid
    assert len(raw_grid_container.lines) == 291
    assert len(raw_grid_container.nodes) == 299


def test_grid_container(gwr):
    grid_container = gwr.grid
    assert len(grid_container.raw_grid.lines) == 291
    assert len(grid_container.raw_grid.nodes) == 299
    assert len(grid_container.participants.loads) == 496