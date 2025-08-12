from nbconvert.preprocessors import ClearOutputPreprocessor
from traitlets.config import get_config


class CustomClearOutputPreprocessor(ClearOutputPreprocessor):
    def preprocess(self, nb, resources):
        for cell in nb.cells:
            if cell.cell_type == "code":
                cell.execution_count = None

                if "metadata" in cell:
                    cell.metadata = {}

        return nb, resources


c = get_config()
c.Exporter.preprocessors = [CustomClearOutputPreprocessor]
