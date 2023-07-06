from psdm_analysis.models.enums import SystemParticipantsEnum


def test_sp_enum():
    bm = SystemParticipantsEnum.BIOMASS_PLANT
    pv = SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT
    assert bm.has_type() is True
    assert pv.has_type() is False
