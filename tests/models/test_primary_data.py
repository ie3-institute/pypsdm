import pytest

from pypsdm.models.enums import TimeSeriesEnum
from pypsdm.models.primary_data import PrimaryData


@pytest.fixture
def primary_data(input_path):
    return PrimaryData.from_csv(input_path)


def test_reading_of_primary_data(primary_data):
    its_p = "f2bb6e55-01d0-42ce-a62a-ef51857776ca"
    its_pq = "8c04e94e-76b0-4369-a55c-f5e1117fb83e"

    assert its_p in primary_data.time_series
    assert its_pq in primary_data.time_series

    assert primary_data[its_p].entity_type == TimeSeriesEnum.P_TIME_SERIES
    assert primary_data[its_pq].entity_type == TimeSeriesEnum.PQ_TIME_SERIES

    participant_pd = primary_data["9abe950d-362e-4efe-b686-500f84d8f368"]
    assert len(participant_pd.data) == 1
    assert participant_pd.data["p"][0] == 3.999998968803


def test_to_csv(primary_data: PrimaryData, tmpdir):
    tmpdir = str(tmpdir)
    primary_data.to_csv(tmpdir)
    pd_read = PrimaryData.from_csv(tmpdir)
    primary_data.compare(pd_read)
