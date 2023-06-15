import pandas as pd
import pytest

from psdm_analysis.models.input.participant.pv import PhotovoltaicPowerPlants


@pytest.fixture
def sample_pvs():
    data = pd.DataFrame(
        {
            "id": ["1", "2", "3"],
            "operates_from": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "operates_until": ["2023-12-31", "2023-12-31", "2023-12-31"],
            "operator": ["operator1", "operator2", "operator3"],
            "node": ["a", "b", "c"],
            "q_characteristic": ["q1", "q2", "q3"],
            "albedo": [0.2, 0.3, 0.4],
            "azimuth": [180, 200, 220],
            "elevation_angle": [30, 45, 60],
            "k_g": [0.5, 0.6, 0.7],
            "k_t": [0.8, 0.9, 1.0],
            "market_reaction": [True, False, True],
            "cos_phi_rated": [0.95, 0.98, 0.99],
        },
        index=["uuid1", "uuid2", "uuid3"],
    )

    return PhotovoltaicPowerPlants(data)


def test_add_entities(sample_pvs, caplog):
    # Create another Entities instance for the test
    other_data = pd.DataFrame(
        {
            "id": ["4", "5"],
            "operates_from": ["2023-03-01", "2023-04-01"],
            "operates_until": ["2023-12-31", "2023-12-31"],
            "operator": ["operator3", "operator4"],
            "node": ["c", "d"],
            "q_characteristic": ["q4", "q5"],
            "albedo": [0.4, 0.5],
            "azimuth": [220, 240],
            "elevation_angle": [50, 60],
            "k_g": [0.7, 0.8],
            "k_t": [0.95, 1.0],
            "market_reaction": [False, True],
            "cos_phi_rated": [0.99, 1.0],
        },
        index=["uuid4", "uuid5"],
    )

    other_pvs = PhotovoltaicPowerPlants(other_data)

    result = sample_pvs + other_pvs

    # Check the resulting Entities instance
    assert len(result) == 5
    assert set(result.data.index) == {"uuid1", "uuid2", "uuid3", "uuid4", "uuid5"}

    # Create another Entities instance with an extra column
    other_data_corrupt = other_data.drop(columns=["cos_phi_rated"])
    other_pvs = PhotovoltaicPowerPlants(other_data_corrupt)

    assert "The two Entities instances have different columns: %s", {
        "cos_phi_rated"
    } in caplog.text


def test_subtract_entities(sample_pvs):
    # Create a subset of sample_pvs to be subtracted
    data_to_subtract = sample_pvs.data.iloc[[2]]
    pvs_to_subtract = PhotovoltaicPowerPlants(data_to_subtract)

    result = sample_pvs - pvs_to_subtract

    assert len(result) == len(sample_pvs) - 1
    assert pvs_to_subtract.data.index[0] not in result.data.index


def test_subtract_with_list_of_indices(sample_pvs):
    indices_to_subtract = ["uuid3"]

    result = sample_pvs - indices_to_subtract

    assert len(result) == len(sample_pvs) - 1
    assert indices_to_subtract[0] not in result.data.index


def test_subtract_with_invalid_indices(sample_pvs):
    invalid_indices = ["uuid3", "uuid4"]  # Indices that don't exist in sample_pvs

    with pytest.raises(
        ValueError,
        match="All indices to remove must exist in the current Entities instance",
    ):
        _ = sample_pvs - invalid_indices


def test_filter_by_nodes(sample_pvs: PhotovoltaicPowerPlants):
    result = sample_pvs.filter_by_nodes(["a", "b"])

    assert len(result) == 2
    assert result.uuid[0] == "uuid1"
    assert result.uuid[1] == "uuid2"

    result = sample_pvs.filter_by_nodes("a")

    assert len(result) == 1
    assert result.uuid[0] == "uuid1"

    assert isinstance(result, PhotovoltaicPowerPlants)


def test_subset(sample_pvs):
    # Test with a single string
    result = sample_pvs.subset("uuid1")
    assert len(result) == 1
    assert result.data.index[0] == "uuid1"

    # Test with a list of strings
    result = sample_pvs.subset(["uuid1", "uuid2"])
    assert len(result) == 2
    assert set(result.data.index) == {"uuid1", "uuid2"}

    # Test with a set of strings
    result = sample_pvs.subset({"uuid1", "uuid2", "uuid3"})
    assert len(result) == 3
    assert set(result.data.index) == {"uuid1", "uuid2", "uuid3"}

    assert isinstance(result, PhotovoltaicPowerPlants)


def test_subset_incorrect(sample_pvs: PhotovoltaicPowerPlants):
    with pytest.raises(
        KeyError,
        match="uuids must be a subset of the current Entities instance. The following uuids couldn't be found: {'not_in_index'}",
    ):
        _ = sample_pvs.subset(["not_in_index"])


def test_subset_id(sample_pvs):
    # Test with a single string
    result = sample_pvs.subset_id("1")
    assert len(result) == 1
    assert result.data["id"][0] == "1"

    # Test with a list of strings
    result = sample_pvs.subset_id(["1", "2"])
    assert len(result) == 2
    assert set(result.data["id"]) == {"1", "2"}

    # Test with a set of strings
    result = sample_pvs.subset_id({"1", "2", "3"})
    assert len(result) == 3
    assert set(result.data["id"]) == {"1", "2", "3"}

    assert isinstance(result, PhotovoltaicPowerPlants)


def test_subset_split(sample_pvs):
    subset1, subset2 = sample_pvs.subset_split(["uuid1", "uuid2"])

    # Test the first subset
    assert len(subset1) == 2
    assert set(subset1.data.index) == {"uuid1", "uuid2"}

    # Test the second subset
    assert len(subset2) == 1
    assert subset2.data.index[0] == "uuid3"


def test_copy_method(sample_pvs):
    # Define the changes you want to apply
    changes = {
        "data": pd.DataFrame(
            {
                "id": ["4"],
                "operates_from": ["2024-01-01"],
                "operates_until": ["2024-12-31"],
                "operator": ["operator4"],
                "node": ["d"],
                "q_characteristic": ["q4"],
                "albedo": [0.5],
                "azimuth": [240],
                "elevation_angle": [75],
                "k_g": [0.8],
                "k_t": [1.1],
                "market_reaction": [False],
                "cos_phi_rated": [0.97],
            },
            index=["uuid4"],
        )
    }

    # Create a copy with changes
    copied = sample_pvs.copy(**changes)

    # Assert that changes were applied correctly
    pd.testing.assert_frame_equal(copied.data, changes["data"])

    # Assert that original was not affected
    assert "4" not in sample_pvs.data["id"].values

    # Test deep copy by modifying original after copying
    sample_pvs.data["id"]["uuid1"] = "10"

    # Assert that the copied data is not affected
    assert copied.data["id"]["uuid1"] == "1"

    # Test shallow copy
    shallow_copied = sample_pvs.copy(deep=False)

    # Modify original after copying
    sample_pvs.data["id"]["uuid1"] = "20"

    # Assert that the shallow copied data is affected
    assert shallow_copied.data["id"]["uuid1"] == "20"
