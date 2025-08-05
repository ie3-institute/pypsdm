import pytest

from pypsdm.io.utils import ROOT_DIR

def test_notebook_check_notebook_except_skipped_cells():
    args = [
        "--nbval",
        "-v",
        ROOT_DIR + "/docs/nbs/input_models.ipynb",
        ROOT_DIR + "/docs/nbs/result_models.ipynb",
    ]

    exit_code = pytest.main(args)

    # Check if there were any failures
    if exit_code != 0:
        raise Exception(f"Notebook tests failed with exit code {exit_code}.")


def test_notebook_only_for_errors_and_explicit_cell_checks():
    # only checking for errors in notebook, unless cell is marked for deeper check
    args = [
        "--nbval-lax",
        "-v",
        ROOT_DIR + "/docs/nbs/plotting_utilities.ipynb",
        ROOT_DIR + "/docs/nbs/plotting_utilities_colormap_lines_and_nodes.ipynb",
        ROOT_DIR + "/docs/nbs/plotting_utilities_colormap_lines.ipynb",
        ROOT_DIR + "/docs/nbs/plotting_utilities_colormap_nodes.ipynb",
    ]

    exit_code = pytest.main(args)

    # Check if there were any failures
    if exit_code != 0:
        raise Exception(f"Notebook tests failed with exit code {exit_code}.")

