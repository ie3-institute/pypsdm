import pytest

@pytest.fixture
def primary_data(gwr):
    return gwr.grid.primary_data

def test_reading_of_primary_data(primary_data):
    participant_pd = primary_data.get_for_participant("9abe950d-362e-4efe-b686-500f84d8f368")
    assert len(participant_pd.data) == 1
    assert participant_pd.data["p"][0] == 3.999998968803
