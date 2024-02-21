from pypsdm.models.enums import SystemParticipantsEnum
from pypsdm.models.result.participant.flex_options import FlexOptionsResult


def test_from_to_csv(gwr, tmp_path):
    flex_res = gwr.results.participants.flex
    assert len(flex_res) == 1
    flex_res.to_csv(tmp_path, mkdirs=True)
    flex_res_from = FlexOptionsResult.from_csv(
        SystemParticipantsEnum.FLEX_OPTIONS, tmp_path
    )
    assert flex_res == flex_res_from
