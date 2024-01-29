import os
import shutil
import tempfile

import pytest

from pypsdm.db.utils import dir_is_empty


@pytest.fixture
def temp_dir():
    # Setup: create a temporary directory
    directory = tempfile.mkdtemp()
    yield directory
    # Teardown: remove the directory after the test is done
    shutil.rmtree(directory)


def create_file(directory, filename):
    file_path = os.path.join(directory, filename)
    open(file_path, "a").close()


def test_empty_directory(temp_dir):
    assert dir_is_empty(temp_dir)


def test_directory_with_ignored_files(temp_dir):
    # Create files that should be ignored
    for filename in [".DS_Store", "metadata.json"]:
        create_file(temp_dir, filename)

    assert dir_is_empty(temp_dir, ignore=[".DS_Store", "metadata.json"])


def test_directory_with_non_ignored_file(temp_dir):
    # Create a file that should not be ignored
    create_file(temp_dir, "testfile.txt")
    assert not dir_is_empty(temp_dir)


def test_directory_with_subdirectory(temp_dir):
    # Create a subdirectory
    sub_dir = os.path.join(temp_dir, "subdir")
    os.mkdir(sub_dir)
    create_file(sub_dir, "testfile.txt")
    assert not dir_is_empty(temp_dir)


def test_empty_subdirectory(temp_dir):
    # Create an empty subdirectory
    sub_dir = os.path.join(temp_dir, "subdir")
    os.mkdir(sub_dir)
    assert dir_is_empty(
        temp_dir
    )  # Directory with an empty subdirectory is considered empty
