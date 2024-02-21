from pypsdm.models.gwr import GridWithResults
from pypsdm.models.result.container.grid import GridResultContainer


def test_to_csv(gwr: GridWithResults, tmp_path, simulation_end):
    grid = gwr.results
    grid.to_csv(
        tmp_path,
    )
    grid_b = GridResultContainer.from_csv(
        tmp_path,
        ",",
        simulation_end=simulation_end,
    )
    grid.compare(grid_b)
