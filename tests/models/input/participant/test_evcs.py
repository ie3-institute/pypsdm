from pypsdm.models.input.participant.evcs import EvChargingStations


def test_to_csv(input_path, tmp_path):
    evcs = EvChargingStations.from_csv(input_path)
    evcs.to_csv(tmp_path)
    evcs_b = EvChargingStations.from_csv(tmp_path)
    evcs.compare(evcs_b)
