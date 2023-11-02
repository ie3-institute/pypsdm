from pypsdm.models.input.participant.evcs import EvChargingStations


def test_to_csv(input_path, delimiter, tmp_path):
    evcs = EvChargingStations.from_csv(input_path, delimiter)
    evcs.to_csv(tmp_path, delimiter)
    evcs_b = EvChargingStations.from_csv(tmp_path, delimiter)
    evcs.compare(evcs_b)
