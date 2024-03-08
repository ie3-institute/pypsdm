from pypsdm import Transformers2W


def test_to_csv(input_path, tmp_path):
    transformer = Transformers2W.from_csv(input_path)
    transformer.to_csv(tmp_path)
    transformer_b = Transformers2W.from_csv(tmp_path)
    transformer.compare(transformer_b)
