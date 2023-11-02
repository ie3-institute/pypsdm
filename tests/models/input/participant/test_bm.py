from pypsdm.models.input.participant.bm import BiomassPlants


def test_to_csv(input_path, delimiter, tmp_path):
    bm = BiomassPlants.from_csv(input_path, delimiter)
    bm.to_csv(tmp_path, delimiter=delimiter)
    bm_b = BiomassPlants.from_csv(tmp_path, delimiter)
    bm.compare(bm_b)
