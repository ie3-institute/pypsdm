from pypsdm.models.input.participant.em import EnergyManagementSystems


def test_to_csv(input_path, tmp_path):
    ems = EnergyManagementSystems.from_csv(input_path)
    ems.to_csv(tmp_path)
    ems_b = EnergyManagementSystems.from_csv(tmp_path)
    ems.compare(ems_b)
