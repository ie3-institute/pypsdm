from pypsdm.models.input.participant.wec import WindEnergyConverters


def test_to_csv(input_path, tmp_path):
    wecs = WindEnergyConverters.from_csv(input_path)
    wecs.to_csv(tmp_path)
    wecs_b = WindEnergyConverters.from_csv(tmp_path)
    wecs.compare(wecs_b)
