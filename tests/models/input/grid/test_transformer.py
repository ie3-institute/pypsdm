from pypsdm.models.input.connector.transformer import Transformers2W


def test_to_csv(input_path, delimiter, tmp_path):
    transformer = Transformers2W.from_csv(input_path, delimiter)
    transformer.to_csv(tmp_path, delimiter)
    transformer_b = Transformers2W.from_csv(tmp_path, delimiter)
    transformer.compare(transformer_b)
