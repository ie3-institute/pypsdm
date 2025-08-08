from pypsdm.models.input.participant.em import EnergyManagementSystems


def test_to_csv(input_path, tmp_path):
    controlling_ems = EnergyManagementSystems.from_csv(input_path)
    controlling_ems.to_csv(tmp_path)
    controlling_ems_b = EnergyManagementSystems.from_csv(tmp_path)
    controlling_ems.compare(controlling_ems_b)
