import os

from pyhocon import ConfigFactory, HOCONConverter

from pypsdm.db.gwr import (
    DB_ENV_VAR,
    GRID_ID_REGEX,
    RESULT_DATE_REGEX,
    RESULT_ID_REGEX,
    LocalGwrDb,
)

# TODO: Write tets for LocalGwrDb (include creation utils from tests/db/utils)


def test_regex():
    assert GRID_ID_REGEX.match("my_grid-v1")
    assert GRID_ID_REGEX.match("my_grid_v1") is None
    assert GRID_ID_REGEX.match("my_grid_1") is None

    assert RESULT_DATE_REGEX.match("2023_11_23")
    assert RESULT_DATE_REGEX.match("2023_11_23-1")

    assert RESULT_ID_REGEX.match("2023_11_23-my_grid-v1")
    assert RESULT_ID_REGEX.match("2023_11_23-1-my_grid-v1")
    assert RESULT_ID_REGEX.match("2023_11_23-1-my_grid-v1-my_suffix")


def test_match_grid_id():
    name, version = "my_grid", 1
    match = LocalGwrDb.match_grid_id(f"{name}-v{version}")
    if match:
        assert match[0] == name
        assert match[1] == version
    else:
        assert ValueError("Invalid grid id")


def test_match_result_date():
    date = "2023_11_23"
    versioned_date = f"{date}-1"
    match = RESULT_DATE_REGEX.match(f"{versioned_date}")
    if match:
        assert len(match.groups()) == 1
        assert match.groups()[0] == date
    else:
        assert ValueError("Invalid grid id")


def test_match_res_id():
    date, grid_id = "2023_11_23", "my_grid-v1"
    versioned_date = f"{date}-1"
    match = LocalGwrDb.match_res_id(f"{versioned_date}-{grid_id}")
    if match:
        assert match[0] == date
        assert match[1] == grid_id
        assert match[2] is None
    else:
        assert ValueError("Invalid result id")

    match = LocalGwrDb.match_res_id(f"20231123-{grid_id}")
    assert match is None

    suffix = "my_suffix"
    match = LocalGwrDb.match_res_id(f"2023_11_23-{grid_id}-{suffix}")
    if match:
        assert match[0] == date
        assert match[1] == grid_id
        assert match[2] == suffix
    else:
        assert ValueError("Invalid result id")


def test_load_from_env_var(tmp_path):
    # set env var
    os.environ[DB_ENV_VAR] = str(tmp_path)
    db = LocalGwrDb()
    assert str(db.path) == str(tmp_path)


def test_read_conf(resources_path):
    conf_path = os.path.join(resources_path, "vn_simona", "vn_simona.conf")
    conf = ConfigFactory.parse_file(conf_path)
    out = HOCONConverter.to_hocon(conf)
    print("out: ", out)
