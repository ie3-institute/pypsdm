from pypsdm.models.input.participant.hp import HeatPumps


def test_to_csv_for_empty(tmp_path, delimiter):
    hps = HeatPumps.create_empty()
    hps.to_csv(tmp_path, delimiter)
    hps_b = HeatPumps.from_csv(tmp_path, delimiter)
    hps.compare(hps_b)
