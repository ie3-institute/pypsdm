from psdm_analysis.models.primary_data import PrimaryData
from tests import utils


def test_reading_of_primary_data():
    pd = PrimaryData.from_csv(utils.VN_SIMONA_INPUT_PATH, utils.VN_SIMONA_DELIMITER)
    participant_pd = pd.get_for_participant("9abe950d-362e-4efe-b686-500f84d8f368")
    assert len(participant_pd.data) == 1
    assert participant_pd.data["p"][0] == 3.999998968803
