import pandas as pd
import pytest

from psdm_analysis.models.input.connector.switches import Switches


@pytest.fixture
def sample_switches():
    data = pd.DataFrame(
        {
            "id": ["1", "2"],
            "operates_from": ["2023-01-01", "2023-02-01"],
            "operates_until": ["2023-12-31", "2023-12-31"],
            "operator": ["operator1", "operator2"],
            "node_a": ["a", "b"],
            "node_b": ["c", "d"],
            "parallel_devices": [0, 0],
            "closed": [False, False],
        },
        index=["uuid1", "uuid2"],
    )

    return Switches(data)


def test_add_entities(sample_switches):
    # Create another Entities instance for the test
    other_data = pd.DataFrame(
        {
            "id": ["3", "4"],
            "operates_from": ["2023-03-01", "2023-04-01"],
            "operates_until": ["2023-12-31", "2023-12-31"],
            "operator": ["operator3", "operator4"],
            "node_a": ["a", "b"],
            "node_b": ["c", "d"],
            "parallel_devices": [0, 0],
            "closed": [False, False],
        },
        index=["uuid3", "uuid4"],
    )

    other_switches = Switches(other_data)

    result = sample_switches + other_switches

    # Check the resulting Entities instance
    assert len(result) == 4
    assert set(result.uuids) == {"uuid1", "uuid2", "uuid3", "uuid4"}
    assert set(result.ids) == {"1", "2", "3", "4"}

    # Create another Entities instance with an extra column
    other_data_corupt = other_data.copy()
    other_data_corupt["extra"] = ["extra1", "extra2"]
    other_switches = Switches(other_data_corupt)

    with pytest.raises(ValueError, match="Columns of the dataframes are not the same"):
        _ = sample_switches + other_switches


def test_subtract_entities(sample_switches):
    # Create a subset of sample_switches to be subtracted
    data_to_subtract = sample_switches.data.iloc[[1]]
    switches_to_subtract = Switches(data_to_subtract)

    result = sample_switches - switches_to_subtract

    assert len(result) == len(sample_switches) - 1
    assert switches_to_subtract.uuids[0] not in result.uuids


def test_subtract_with_list_of_indices(sample_switches):
    indices_to_subtract = ["uuid2"]

    result = sample_switches - indices_to_subtract

    assert len(result) == len(sample_switches) - 1
    assert indices_to_subtract[0] not in result.uuids


def test_subtract_with_invalid_indices(sample_switches):
    invalid_indices = ["uuid3", "uuid4"]  # Indices that don't exist in sample_switches

    with pytest.raises(
        ValueError,
        match="All indices to remove must exist in the current Entities instance",
    ):
        _ = sample_switches - invalid_indices
