from pypsdm.models.input.participant.hp import HeatPumps


def test_to_csv(input_path_sg, tmp_path):
    hps = HeatPumps.from_csv(input_path_sg)
    hps.to_csv(tmp_path)
    hps_b = HeatPumps.from_csv(tmp_path)
    hps.compare(hps_b)
