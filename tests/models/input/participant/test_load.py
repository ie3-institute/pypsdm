from pypsdm.models.input.participant.load import Loads


def test_to_csv(input_path, tmp_path):
    load = Loads.from_csv(input_path)
    load.to_csv(tmp_path)
    load_b = Loads.from_csv(tmp_path)
    load.compare(load_b)
