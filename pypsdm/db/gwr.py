import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pypsdm.db.utils import PathManagerMixin
from pypsdm.models.gwr import GridWithResults
from pypsdm.models.input import GridContainer
from pypsdm.models.result import GridResultContainer

# Grid id naming strategy
# [grid id]-v[version number]
# e.g. my_grid-v1
GRID_ID_REGEX = re.compile(r"(\w+)-v(\d+)")

# Simulation result folder naming strategy
# [date[optional increment]]-[GRID_ID_REGEX][-optional suffix]
# e.g. 2023_11_23-1-my_grid-v1-my_suffix
RESULT_DATE_REGEX = re.compile(r"(\d{4}_\d{2}_\d{2})(?:-\d+)?")
RESULT_SUFFIX_REGEX = re.compile(r"(?:-([\w-]+))?")
RESULT_ID_REGEX = re.compile(
    r"{}-({}){}".format(
        RESULT_DATE_REGEX.pattern, GRID_ID_REGEX.pattern, RESULT_SUFFIX_REGEX.pattern
    )
)


@dataclass
class LocalGwrDb(PathManagerMixin):
    """
    Local database that keeps track of grid models and and corresponding results.
    Offers methods to read grids, results as well as grid with results. Also
    contains methods to add grids and results to the database.

    All storage paths are relative to its path attribute.

    Args:
        path (Path): Base path to database.
    """

    path: Path

    def __init__(self, path: str | Path):
        self.path = Path(path) if isinstance(path, str) else path

    @property
    def grids_path(self) -> Path:
        return self.path.joinpath("grids")

    @property
    def results_path(self) -> Path:
        return self.path.joinpath("results")

    def additional_paths(self) -> list[Path]:
        return [self.path, self.grids_path, self.results_path]

    def list_grids(self, grid_id: str | None = None, path=False) -> list[str]:
        """
        List all managed grid ids. Only lists directories that are valid grid ids.
        Valid grid ids are specified by GRID_ID_REGEX
        """
        grids = os.listdir(self.grids_path)
        grids.sort(reverse=True)
        # ignore hidden files or directories
        grids = [grid for grid in grids if not grid.startswith(".")]
        if grid_id:
            filtered = []
            for grid in grids:
                match = self.match_grid_id(grid_id)
                if match:
                    grid_id, _ = match
                    if grid_id == grid_id:
                        filtered.append(grid)
            grids = filtered
        if path:
            grids = [str(self.grids_path.joinpath(grid)) for grid in grids]
        return grids

    def list_grid_results(self, grid_id: str | None = None) -> list[str]:
        """
        List all grid results. If grid_id is specified, only results for this grid are
        returned. Grids are sorted by date, most recent first.
        """
        results = os.listdir(self.results_path)
        results.sort(reverse=True)
        # ignore hidden files or directories
        results = [res for res in results if not res.startswith(".")]
        if grid_id:
            filtered = []
            for res in results:
                match = self.match_res_id(res)
                if match:
                    _, grid_id, _ = match
                    if grid_id == grid_id:
                        filtered.append(res)
            results = filtered
        return results

    def read_gwr_most_recent(self, grid_id) -> GridWithResults:
        """Read most recent GridWithResults."""
        result = self.list_grid_results(grid_id)[0]
        return self.read_gwr(result)

    def read_gwr(self, res_id: str) -> GridWithResults:
        """Read GridWithResults."""
        res_path = os.path.join(self.results_path, res_id, "rawOutputData")
        res_id_match = self.match_res_id(res_id)
        if res_id_match:
            _, grid_id, _ = res_id_match
        else:
            raise ValueError(
                f"Invalid res_id: {res_id}, expected format: {RESULT_ID_REGEX.pattern}"
            )

        grid_path = os.path.join(self.grids_path, grid_id)
        if not os.path.exists(grid_path):
            raise FileNotFoundError(
                f"Grid with id {grid_id} does not exist at {grid_path}."
            )

        return GridWithResults.from_csv(
            name=grid_id,
            grid_path=grid_path,
            result_path=res_path,
        )

    def read_grid(self, identifier: str) -> GridContainer:
        """
        Read grid from identifier. Identifier can be either grid id or result id.
        If result id is given, the corresponding grid is returned.

        Args:
            identifier (str): Grid or result identifier.

        Returns:
            GridContainer: GridContainer instance.
        """
        # check if grid or result id
        if identifier in self.list_grids():
            grid_id = identifier
        elif identifier in self.list_grid_results():
            match = self.match_res_id(identifier)
            if match:
                _, grid_id = match
            else:
                raise ValueError(
                    f"Invalid result dentifier: {identifier}. Expected format: {RESULT_ID_REGEX.pattern}"
                )
        else:
            raise ValueError(
                f"Invalid identifier: {identifier}. Expected either grid or result identifier."
            )
        return GridContainer.from_csv(
            str(self.grids_path.joinpath(grid_id)),
            delimiter=",",
        )

    def read_results(self, res_id: str):
        """Read results from res_id."""
        return GridResultContainer.from_csv(
            res_id,
            str(self.results_path.joinpath(res_id)),
            delimiter=",",
        )

    def add_grid_from_path(
        self, grid_path: str | Path, grid_name: str, version: int = 1, move=False
    ):
        """
        Adds grid from path to local "database". If move is True, the grid is moved to the
        databases source path, otherwise it is copied.

        Args:
            grid_path (str | Path): Path to grid.
            grid_name (str): Grid name.
            version (int): Grid version. Defaults to 1.
            move (bool, optional): Move grid to database source path. Defaults to False.

        Returns:
            The created grid id
        """
        versioned_id = f"{grid_name}-v{version}"
        match = GRID_ID_REGEX.match(versioned_id)
        if not match:
            raise ValueError(
                f"Invalid grid_id: {grid_name}, expected format: {GRID_ID_REGEX.pattern}"
            )
        destination_dir = self.grids_path.joinpath(versioned_id)
        if destination_dir.exists():
            raise FileExistsError(f"Grid with id {versioned_id} already exists.")
        if move:
            os.rename(grid_path, destination_dir)
        else:
            shutil.copytree(grid_path, destination_dir)
        return versioned_id

    def add_results_from_path(
        self,
        results_path: str | Path,
        versioned_grid_id: str,
        date: datetime | None = None,
        move=False,
    ):
        """
        Adds results from path to local "database". If move is True, the results are moved to the
        databases source path, otherwise they are copied.
        NOTE: There needs to be a grid with the given versioned_grid_id in the database.

        Args:
            results_path (str | Path): Path to results.
            versioned_grid_id (str): Versioned grid id.
            date (datetime, optional): Date of results. Defaults to None.
            move (bool, optional): Move results to database source path. Defaults to False.
        """
        versioned_grid_id_match = GRID_ID_REGEX.match(versioned_grid_id)
        if not versioned_grid_id_match:
            raise ValueError(
                f"Invalid grid_id: {versioned_grid_id}, expected format: {GRID_ID_REGEX.pattern}"
            )

        # Check if corresponding grid exists
        grid_path = self.grids_path.joinpath(versioned_grid_id)
        if not grid_path.exists():
            raise FileNotFoundError(
                f"Grid with id {versioned_grid_id} does not exist. Please add grid first."
            )

        # Check if results are present where expected
        raw_output_path = os.path.join(results_path, "rawOutputData")
        if not os.path.exists(raw_output_path):
            raise FileNotFoundError(f"Expected results at {raw_output_path}.")

        if not date:
            # Get date where result folder was created
            raw_output_path_stat = os.stat(raw_output_path)
            date = datetime.fromtimestamp(raw_output_path_stat.st_mtime)

        # Add result data
        res_id = self.create_res_id(versioned_grid_id, date)
        destination_dir = self.results_path.joinpath(res_id)
        if destination_dir.exists():
            raise FileExistsError(f"Results with id {res_id} already exists.")
        if move:
            os.rename(results_path, destination_dir)
        else:
            shutil.copytree(results_path, destination_dir)

    @staticmethod
    def match_grid_id(grid_id) -> tuple[str, str] | None:
        """Matches grid_id and returns grid_id and grid_version or None."""
        match = GRID_ID_REGEX.match(grid_id)
        if match:
            grid_id, grid_version = match.groups()
            return grid_id, grid_version
        else:
            return None

    @staticmethod
    def match_res_id(res_id: str) -> tuple[str, str, str | None] | None:
        """Match res_id and return date, grid_id and grid_version or None."""
        match = RESULT_ID_REGEX.match(res_id)
        if match:
            date, grid_id, *_, suffix = match.groups()
            return date, grid_id, suffix
        else:
            return None

    @staticmethod
    def create_grid_id(grid_id: str, version: int = 1) -> str:
        grid_id = f"{grid_id}-v{version}"
        match = GRID_ID_REGEX.match(grid_id)
        assert match, f"Invalid grid_id: {grid_id}"
        return grid_id

    @staticmethod
    def create_res_id(grid_id: str, date: datetime) -> str:
        res_id = f"{date.strftime('%Y_%m_%d')}-{grid_id}"
        match = RESULT_ID_REGEX.match(res_id)
        assert match, f"Invalid res_id: {res_id}"
        return res_id
