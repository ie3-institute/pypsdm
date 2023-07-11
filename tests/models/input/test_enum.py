from psdm_analysis.models.enums import (RawGridElementsEnum,
                                        SystemParticipantsEnum)


def test_entities_enum():
    assert not SystemParticipantsEnum.LOAD.has_type()
    assert RawGridElementsEnum.LINE.has_type()


def test_get_plot_name():
    actual = SystemParticipantsEnum.FIXED_FEED_IN.get_plot_name()
    assert actual == "Fixed Feed In"
