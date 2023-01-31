from psdm_analysis.models.input.container.grid_container import (
    RawGridContainer,
    GridContainer,
)
from tests import utils


def test_raw_grid_container():
    raw_grid_container = RawGridContainer.from_csv(
        utils.VN_SIMONA_INPUT_PATH, utils.VN_SIMONA_DELIMITER
    )
    assert len(raw_grid_container.lines) == 291
    assert len(raw_grid_container.nodes) == 299


def test_grid_container():
    grid_container = GridContainer.from_csv(
        utils.VN_SIMONA_INPUT_PATH, utils.VN_SIMONA_DELIMITER
    )
    assert len(grid_container.raw_grid.lines) == 291
    assert len(grid_container.raw_grid.nodes) == 299
    assert len(grid_container.participants.loads) == 496
