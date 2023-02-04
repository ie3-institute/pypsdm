from psdm_analysis.models.input.enums import RawGridElementsEnum, SystemParticipantsEnum


def test_entities_enum():
    assert SystemParticipantsEnum.LOAD.has_type() == False
    assert RawGridElementsEnum.LINE.has_type() == True


def test_get_plot_name():
    actual = SystemParticipantsEnum.FIXED_FEED_IN.get_plot_name()
    assert actual == "Fixed Feed In"
