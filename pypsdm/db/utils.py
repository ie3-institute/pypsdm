import os
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path


def open_in_file_explorer(path):
    """
    Opens the file explorer at the given path based on the operating system.

    Args:
        path (str): The file path to open in the file explorer.

    Returns:
        None
    """
    # Normalize the path
    # TODO: This might not work as expected when using symlinks
    normalized_path = os.path.normpath(path)
    if not os.path.exists(normalized_path):
        raise FileNotFoundError(f"The path {normalized_path} does not exist.")

    # Windows
    if sys.platform.startswith("win"):
        subprocess.run(["explorer", normalized_path])
    # macOS
    elif sys.platform.startswith("darwin"):
        subprocess.run(["open", normalized_path])
    # Linux - using Nautilus (GNOME)
    elif sys.platform.startswith("linux"):
        subprocess.run(["nautilus", normalized_path])
    else:
        raise Exception(f"Unsupported operating system: {sys.platform}")


def dir_is_empty(dir_path, ignore_symlinks=True, ignore=[]):
    """
    Helper method to check if a directory is empty. A directory is considered
    empty if it does not contain any files except for the ones that are ignored
    and all its subdirectories are empty according to the same definition.
    """
    for root, dirs, files in os.walk(dir_path):
        files = [f for f in files if f not in ignore]
        if ignore_symlinks:
            files = [f for f in files if not os.path.islink(os.path.join(root, f))]

        if files:
            return False

        dirs[:] = [
            d
            for d in dirs
            if not dir_is_empty(os.path.join(root, d), ignore_symlinks, ignore)
        ]

    return True


def directory_size_kb(path):
    """
    Calculate the total size of a directory recursively including all its files and
    subdirectories. Result is returned in kilobytes.
    """
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if not os.path.islink(filepath):  # Skip if it's a symbolic link
                total_size += os.path.getsize(filepath)
    return total_size / 1024


def create_symlink(source: Path, target: Path):
    if not target.exists():
        os.symlink(source, target)
    else:
        raise FileExistsError(f"Symlink {target} already exists")


class PathManagerMixin(ABC):
    """
    Mixin to deal with local directories. See LocalGwrDb for application example.
    """

    def initialize_file_tree(self) -> None:
        """Initialize all paths that are managed by the class."""
        paths = self.get_all_paths()
        for path in paths:
            os.makedirs(path, exist_ok=True)

    def get_all_paths(self) -> list[Path]:
        """Returns a list of all paths that are managed by the class"""
        all_paths = []
        for cls in self.__class__.__mro__:
            if issubclass(cls, PathManagerMixin):
                try:
                    all_paths.extend(cls.additional_paths(self))
                except NotImplementedError:
                    continue
        return all_paths

    @abstractmethod
    def additional_paths(self) -> list[Path]:
        """Additional paths the mixin adds to the Experiment."""
        return []

    def open_in_file_explorer(self, path=None) -> None:
        """
        Open in file explorer. If no path is given, the base path of the class
        is opened.
        """
        path = self.path if path is None else path  # type: ignore
        open_in_file_explorer(self.path)  # type: ignore
