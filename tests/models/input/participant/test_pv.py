from pypsdm.models.input.participant.pv import PhotovoltaicPowerPlants


def test_to_csv(input_path, tmp_path):
    pvs = PhotovoltaicPowerPlants.from_csv(input_path)
    pvs.to_csv(tmp_path)
    pvs_b = PhotovoltaicPowerPlants.from_csv(tmp_path)
    pvs.compare(pvs_b)
