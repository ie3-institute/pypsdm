from pypsdm.models.input.participant.load import Loads


def test_to_csv(input_path, delimiter, tmp_path):
    load = Loads.from_csv(input_path, delimiter)
    load.to_csv(tmp_path, delimiter=delimiter)
    load_b = Loads.from_csv(tmp_path, delimiter)
    load.compare(load_b)
