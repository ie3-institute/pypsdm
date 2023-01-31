from datetime import datetime

EMPTY_GRID_PATH = "/tests/resources/empty_grid"
VN_SIMONA_INPUT_PATH = "tests/resources/vn_simona/input"
VN_SIMONA_RESULT_PATH = "tests/resources/vn_simona/results"
VN_SIMONA_DELIMITER = ","
VN_SIMULATION_START = datetime(year=2011, month=1, day=1, hour=12)
VN_SIMULATION_END = datetime(year=2011, month=1, day=1, hour=14)
TEST_NODE_UUID = "401f37f8-6f2c-4564-bc78-6736cb9cbf8d"


def is_close(a, b, rel_tol=1e-09):
    return abs(a - b) <= rel_tol
