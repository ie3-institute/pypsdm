from pypsdm.models.input.participant.evs import ElectricVehicles


def test_to_csv(input_path, delimiter, tmp_path):
    ev = ElectricVehicles.from_csv(input_path, delimiter)
    ev.to_csv(tmp_path, delimiter=delimiter)
    ev_b = ElectricVehicles.from_csv(tmp_path, delimiter)
    ev.compare(ev_b)
