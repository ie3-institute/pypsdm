# psdm-analysis

The psdm-analysis tool is meant to parse the [Power System Data Model (PSDM)](https://github.com/ie3-institute/PowerSystemDataModel) as well as provide calculation and plotting utilities to analyze the respective data.

It is currently under development. So if you want to use it, expect it to change quite frequently for now.

## Installation

To add the project as dependency run 
```console
pip install pypsdm
```
or 
```console
poetry add pypsdm
```
depending on your depedency management system. 

If you want to clone and explore the repository locally, run
```console
poetry install 
```
inside the repository root folder.
For more information about poetry, refer to their [documentation](https://python-poetry.org/docs/).

## Documentation

Please refer to:

- `docs/nbs/input_models.ipynb`
- `docs/nbs/result_models.ipynb`
- `docs/nbs/plotting_utilities.ipynb`

to see exemplary notebooks outlining some of the basic functionalities.

## Quickstart:

You can read grid models via

```python
from pypsdm.models.gwr import GridWithResults

grid_path = "/path/to/my/psdm/grid"
result_path = "/path/to/my/psdm/results"

gwr = GridWithResults.from_csv(grid_path, result_path)
```

If you only want to read the grid model without the results 

```python
# All relevant input models can be imported from `pypsdm/models/input`
from pypsdm.models.input import GridContainer

grid_path = "/path/to/my/psdm/grid"
grid = GridContainer.from_csv(grid_path)
```

If you only want to read the results without the grid model

```python
# All relevant result models can be imported from `pypsdm/models/result`
from pypsdm.models.results import GridResultContainer

result_path = "/path/to/my/psdm/results"
results = GridResultContainer.from_csv(result_path)
```

## Known Issues

- When adding the project as a dependency the language server of the code editors do not 
suggest autoimports for all symbols of the project, which means they have to be imported
manually. It might  have something to do with how poetry publishes the artifacts. If you
have an idea what the issue could be any tipps are welcome.