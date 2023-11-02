from pypsdm.models.input.participant.pv import PhotovoltaicPowerPlants


def test_to_csv(input_path, delimiter, tmp_path):
    pvs = PhotovoltaicPowerPlants.from_csv(input_path, delimiter)
    pvs.to_csv(tmp_path, delimiter)
    pvs_b = PhotovoltaicPowerPlants.from_csv(tmp_path, delimiter)
    pvs.compare(pvs_b)
