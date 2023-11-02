from pypsdm.models.input.participant.storage import Storages


def test_to_csv(input_path, delimiter, tmp_path):
    storages = Storages.from_csv(input_path, delimiter)
    storages.to_csv(tmp_path, delimiter)
    storage_b = Storages.from_csv(tmp_path, delimiter)
    storages.compare(storage_b)
