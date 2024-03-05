from pypsdm.models.input.participant.storage import Storages


def test_to_csv(input_path, tmp_path):
    storages = Storages.from_csv(input_path)
    storages.to_csv(tmp_path)
    storage_b = Storages.from_csv(tmp_path)
    storages.compare(storage_b)
