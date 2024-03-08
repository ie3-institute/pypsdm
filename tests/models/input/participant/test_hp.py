from pypsdm.models.input.participant.hp import HeatPumps


def test_to_csv_for_empty(tmp_path):
    hps = HeatPumps.create_empty()
    hps.to_csv(tmp_path)
    hps_b = HeatPumps.from_csv(tmp_path)
    hps.compare(hps_b)
