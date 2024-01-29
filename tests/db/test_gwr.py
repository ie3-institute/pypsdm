from pypsdm.db.gwr import GRID_ID_REGEX, RESULT_DATE_REGEX, RESULT_ID_REGEX, LocalGwrDb


def test_regex():
    assert GRID_ID_REGEX.match("my_grid-v1")
    assert GRID_ID_REGEX.match("my_grid_v1") is None
    assert GRID_ID_REGEX.match("my_grid_1") is None

    assert RESULT_DATE_REGEX.match("2023_11_23")
    assert RESULT_DATE_REGEX.match("2023_11_23-1")

    assert RESULT_ID_REGEX.match("2023_11_23-my_grid-v1")
    assert RESULT_ID_REGEX.match("2023_11_23-1-my_grid-v1")


def test_match_grid_id():
    name, version = "my_grid", "1"
    match = LocalGwrDb.match_grid_id(f"{name}-v{version}")
    if match:
        assert match[0] == name
        assert match[1] == version
    else:
        assert ValueError("Invalid grid id")


def test_match_res_id():
    date, grid_id = "2023_11_23-01", "my_grid-v1"
    match = LocalGwrDb.match_res_id(f"{date}-{grid_id}")
    if match:
        assert match[0] == date
        assert match[1] == grid_id
    else:
        assert ValueError("Invalid result id")

    match = LocalGwrDb.match_res_id(f"20231123-{grid_id}")
    assert match is None
