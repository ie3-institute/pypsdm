from pypsdm.models.input.participant.em import EnergyManagementSystems


def test_to_csv(input_path, delimiter, tmp_path):
    ems = EnergyManagementSystems.from_csv(input_path, delimiter)
    ems.to_csv(tmp_path, delimiter)
    ems_b = EnergyManagementSystems.from_csv(tmp_path, delimiter)
    ems.compare(ems_b)
