from pypsdm.models.input.participant.evs import ElectricVehicles


def test_to_csv(input_path_sg, tmp_path):
    ev = ElectricVehicles.from_csv(input_path_sg)
    ev.to_csv(tmp_path)
    ev_b = ElectricVehicles.from_csv(tmp_path)
    ev.compare(ev_b)
