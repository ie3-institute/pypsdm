from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.result.participant.flex_options import \
    FlexOptionsResult
from tests import utils


def test_from_csv():
    flex_options_results = FlexOptionsResult.from_csv(
        SystemParticipantsEnum.FLEX_OPTIONS,
        utils.VN_SIMONA_RESULT_PATH,
        utils.VN_SIMONA_DELIMITER,
        utils.VN_SIMULATION_END,
    )
    assert len(flex_options_results) == 1
