from pypsdm.models.input.participant.bm import BiomassPlants


def test_to_csv(input_path, tmp_path):
    bm = BiomassPlants.from_csv(input_path)
    bm.to_csv(tmp_path)
    bm_b = BiomassPlants.from_csv(tmp_path)
    bm.compare(bm_b)
