from pypsdm.models.input.participant.wec import WindEnergyConverters


def test_to_csv(input_path, delimiter, tmp_path):
    wecs = WindEnergyConverters.from_csv(input_path, delimiter)
    wecs.to_csv(tmp_path, delimiter)
    wecs_b = WindEnergyConverters.from_csv(tmp_path, delimiter)
    wecs.compare(wecs_b)
