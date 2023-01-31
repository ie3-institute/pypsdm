from psdm_analysis.models.grid_with_results import GridWithResults
from tests.utils import VN_SIMONA_DELIMITER, VN_SIMONA_RESULT_PATH, VN_SIMONA_INPUT_PATH


def test_grid_with_results():
    data = GridWithResults.from_csv(
        VN_SIMONA_INPUT_PATH,
        VN_SIMONA_DELIMITER,
        VN_SIMONA_RESULT_PATH,
        VN_SIMONA_DELIMITER,
    )
    print()


test_grid_with_results()
