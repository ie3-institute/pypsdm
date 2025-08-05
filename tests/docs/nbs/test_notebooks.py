import pytest

from pypsdm.io.utils import ROOT_DIR


def test_notebook_input_models():
    args = [
        "--nbval",
        "-v",
        ROOT_DIR + "/docs/nbs/input_models.ipynb",
    ]

    exit_code = pytest.main(args)

    # Check if there were any failures
    if exit_code != 0:
        raise Exception(f"Notebook tests failed with exit code {exit_code}.")


def test_notebook_result_models():
    args = [
        "--nbval",
        "-v",
        ROOT_DIR + "/docs/nbs/result_models.ipynb",
    ]

    exit_code = pytest.main(args)

    # Check if there were any failures
    if exit_code != 0:
        raise Exception(f"Notebook tests failed with exit code {exit_code}.")
