from pypsdm.models.input.participant.thermal_storage import ThermalStorages


def test_to_csv(input_path, tmp_path):
    thermal_storages = ThermalStorages.from_csv(input_path)
    thermal_storages.to_csv(tmp_path)
    thermal_storages_b = ThermalStorages.from_csv(tmp_path)
    thermal_storages.compare(thermal_storages_b)
