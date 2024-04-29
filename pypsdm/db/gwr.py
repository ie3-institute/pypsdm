import os
import re
import shutil
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger
from pyhocon import ConfigFactory, ConfigTree, HOCONConverter

from pypsdm.db.utils import PathManagerMixin
from pypsdm.models.gwr import GridWithResults
from pypsdm.models.input.container.grid import GridContainer
from pypsdm.models.result.container.grid import GridResultContainer

# Grid id naming strategy
# [grid id]-v[version number]
# e.g. my_grid-v1
GRID_ID_REGEX = re.compile(r"(\w+)-v(\d+)")

# Simulation result folder naming strategy
# [date[optional increment]]-[GRID_ID_REGEX][-optional suffix]
# e.g. 2023_11_23-1-my_grid-v1-my_suffix
RESULT_DATE_REGEX = re.compile(r"(\d{4}_\d{2}_\d{2})(?:-\d+)?")
RESULT_SUFFIX_REGEX = re.compile(r"(?:-(.+))?")
RESULT_ID_REGEX = re.compile(
    r"{}-({}){}".format(
        RESULT_DATE_REGEX.pattern, GRID_ID_REGEX.pattern, RESULT_SUFFIX_REGEX.pattern
    )
)
DB_ENV_VAR = "LOCAL_GWR_DB"


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

    def __init__(self, path: str | Path | None = None):
        if path is None:
            path = os.environ.get(DB_ENV_VAR)
            if path is None:
                raise ValueError(
                    f"Database path not specified. Set {DB_ENV_VAR} environment variable or pass path as argument."
                )
            if path.startswith("~"):
                path = os.path.expanduser(path)
            path = Path(path).absolute()
        else:
            if path.startswith("~"):
                path = os.path.expanduser(path)
        self.path = Path(path) if isinstance(path, str) else path

    @property
    def grids_path(self) -> Path:
        return self.path.joinpath("grids")

    @property
    def results_path(self) -> Path:
        return self.path.joinpath("results")

    def additional_paths(self) -> list[Path]:
        return [self.path, self.grids_path, self.results_path]

    def get_grid_path(self, identifier: str, should_exist: bool = True) -> Path | None:
        """
        Get grid from identifier. Identifier can be either grid id or result id.
        If result id is given, the corresponding grid is returned.

        Set should_exist to False to get the correct path given the identifier
        even if the grid does not exist. NOTE: In this case the identifier needs
        to be a valid grid id.
        """
        grid_id = None
        if identifier in self.list_grids():
            grid_id = identifier
        if identifier in self.list_results():
            match = self.match_res_id(identifier)
            if match:
                _, grid_id, _ = match
            else:
                raise ValueError(
                    f"Unable to retrieve grid id from result identifier: {identifier}."
                )
        if grid_id is None:
            if should_exist:
                return None
            else:
                if self.match_grid_id(identifier):
                    return self.grids_path.joinpath(identifier)
                else:
                    raise ValueError(
                        f"Invalid grid_id: {identifier}, expected format: {GRID_ID_REGEX.pattern}. See `create_grid_id` to create valid ids"
                    )
        return self.grids_path.joinpath(grid_id)

    def get_result_path(self, res_id: str, should_exist: bool = True) -> Path | None:
        """
        Get result path from res_id. By default returns is none if res_id does not exist.
        Set should_exist to False to get the correct path even if the result does not exist.
        """
        if not self.match_res_id(res_id):
            raise ValueError(
                f"Invalid res_id: {res_id}, expected format: {RESULT_ID_REGEX.pattern}. See `create_res_id` to create valid ids"
            )
        if should_exist:
            if res_id in self.list_results():
                return self.results_path.joinpath(res_id)
            else:
                return None
        return self.results_path.joinpath(res_id)

    def list_grids(self, grid_id: str | None = None, path=False) -> list[str]:
        """
        List all managed grid ids. Only lists directories that are valid grid ids.
        Valid grid ids are specified by GRID_ID_REGEX.

        If a grid_id is given we return all versions of this grid. You can either
        pass only the base id to search for or a versioned id.

        Args:
            grid_id (str, optional): Search for versions of specific grid. Defaults to None.
            path (bool, optional): Return paths instead of ids. Defaults to False.

        Returns:
            list[str]: List of grid ids or paths.
        """

        grids = os.listdir(self.grids_path)
        grids.sort(reverse=True)
        # ignore hidden files or directories
        grids = [grid for grid in grids if not grid.startswith(".")]

        # If a versioned id is given, extract the base id
        if grid_id:
            match = self.match_grid_id(grid_id)
            if match:
                base_id, _ = match
            else:
                base_id = grid_id

            filtered = []
            for grid in grids:
                match = self.match_grid_id(grid)
                if match:
                    name, _ = match
                    if name == base_id:
                        filtered.append(grid)
            grids = filtered

        if path:
            grids = [str(self.grids_path.joinpath(grid)) for grid in grids]
        return grids

    def list_results(self, grid_id: str | None = None) -> list[str]:
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

    def open_configs(self, grid_id: str):
        path = self.get_grid_path(grid_id)
        if path:
            conf_path = path.joinpath("configs")
            if conf_path.exists():
                self.open_in_file_explorer()
            else:
                raise FileNotFoundError(
                    f"No configs for {grid_id} exist in {conf_path}."
                )
        else:
            raise FileNotFoundError(f"Grid with id {grid_id} does not exist.")

    def copy_configs(
        self,
        grid_id: str,
        target_grid_id: str,
        adjust_grid_path: bool = True,
        copy_slack_volt: bool = True,
    ):
        origin_grid_path = self.get_grid_path(grid_id)
        if not origin_grid_path:
            raise FileNotFoundError(f"Grid with id {grid_id} does not exist.")

        origin_conf_path = origin_grid_path.joinpath("configs")
        if not origin_conf_path.exists():
            logger.debug(f"No configs for {grid_id} exist in {origin_conf_path}.")
            return

        target_grid_path = self.get_grid_path(target_grid_id)
        if not target_grid_path:
            raise FileNotFoundError(f"Grid with id {target_grid_id} does not exist.")
        target_conf_path = target_grid_path.joinpath("configs")
        target_conf_path.mkdir(exist_ok=True)

        for file in os.listdir(origin_conf_path):
            conf = ConfigFactory.parse_file(origin_conf_path.joinpath(file))
            if adjust_grid_path:
                conf = self.adjust_conf_path(conf, str(target_grid_path))
            conf = HOCONConverter.to_hocon(conf)
            with open(os.path.join(target_conf_path, file), "w") as f:
                f.write(conf)

        # temporary
        if copy_slack_volt:
            slack_v_path = origin_grid_path.joinpath("slack_volt.csv")
            if slack_v_path.exists():
                shutil.copy(slack_v_path, target_grid_path)

    def read_gwr_most_recent(self, grid_id) -> GridWithResults:
        """Read most recent GridWithResults."""
        result = self.list_results(grid_id)[0]
        return self.read_gwr(result)

    def read_gwr(self, res_id: str) -> GridWithResults:
        """Read GridWithResults."""

        raw_output_path = os.path.join(self.results_path, res_id, "rawOutputData")
        if os.path.exists(raw_output_path):
            res_path = raw_output_path
        else:
            res_path = os.path.join(self.results_path, res_id)
        res_id_match = self.match_res_id(res_id)
        if res_id_match:
            _, grid_id, _ = res_id_match
        else:
            raise ValueError(
                f"Invalid res_id: {res_id}, expected format: {RESULT_ID_REGEX.pattern}"
            )

        grid_path = self.get_grid_path(grid_id)
        if grid_path is None:
            raise FileNotFoundError(
                f"Grid with id {grid_id} does not exist at {grid_path}."
            )

        return GridWithResults.from_csv(
            grid_path=str(grid_path),
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
        grid_path = self.get_grid_path(identifier)
        if grid_path is None:
            raise FileNotFoundError(
                f"Grid or result with id {identifier} does not exist in database."
            )
        return GridContainer.from_csv(
            str(grid_path),
        )

    def read_results(self, res_id: str):
        """Read results from res_id."""
        return GridResultContainer.from_csv(
            res_id,
            str(self.results_path.joinpath(res_id)),
        )

    def add_grid(
        self,
        grid: GridContainer,
        grid_id: str,
        include_primary_data: bool = True,
    ):
        """
        Adds grid to local database.

        Args:
            grid (GridContainer): GridContainer instance.
            version (int): Grid version. Defaults to 1.

        Returns:
            The created grid id
        """
        destination_dir = self.get_grid_path(grid_id, should_exist=False)
        if destination_dir is None:
            raise ValueError("Unable to create grid id.")
        if destination_dir.exists():
            raise FileExistsError(f"Grid with id {grid_id} already exists.")
        os.makedirs(destination_dir)
        grid.to_csv(str(destination_dir), include_primary_data=include_primary_data)
        return grid_id

    def remove_grid(self, grid_id: str, force: bool = False):
        """
        Removes grid from file system.
        ATTENTION: Files will be permanently deleted so use with caution.
        """

        grid_path = self.get_grid_path(grid_id)
        if grid_path is None:
            raise FileNotFoundError(f"Grid with id {grid_id} does not exist.")

        # Do some safety checks
        if not force:
            if not grid_path.parent.name == "grids":
                raise ValueError(
                    f"""Expected grid path to be in grids directory, got {grid_path}.
                    Aborting to prevent accidental deletion. Set force=True to override."""
                )

            for f in os.listdir(grid_path):
                if os.path.isdir(f):
                    raise ValueError(
                        f"""Expected grid path {grid_path} to only contain files,
                        but found directory {f}. Aborting to prevent accidental
                        deletion. Set force=True to override."""
                    )
        shutil.rmtree(grid_path)

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

    def add_results(
        self,
        results: GridResultContainer,
        versioned_grid_id: str,
        suffix: str | None = None,
        date: datetime | None = None,
    ):
        """
        Adds results to local "database".
        NOTE: There needs to be a grid with the given versioned_grid_id in the database.

        Args:
            results (GridResultContainer): GridResultContainer instance.
            versioned_grid_id (str): Versioned grid id.
            date (datetime, optional): Date of results. Defaults to None.
            move (bool, optional): Move results to database source path. Defaults to False.
        """
        versioned_grid_id_match = self.match_grid_id(versioned_grid_id)
        if versioned_grid_id_match is None:
            raise ValueError(
                f"Invalid grid_id: {versioned_grid_id}, expected format: {GRID_ID_REGEX.pattern}"
            )

        # Check if corresponding grid exists
        grid_path = self.grids_path.joinpath(versioned_grid_id)
        if not grid_path.exists():
            raise FileNotFoundError(
                f"Grid with id {versioned_grid_id} does not exist. Please add grid first."
            )

        if not date:
            date = datetime.now()

        # Add result data
        res_id = self.create_res_id(versioned_grid_id, date, suffix)
        destination_dir = self.results_path.joinpath(res_id)
        if destination_dir.exists():
            raise FileExistsError(f"Results with id {res_id} already exists.")
        results.to_csv(str(destination_dir), mkdirs=True)

    def add_results_from_path(
        self,
        results_path: str | Path,
        versioned_grid_id: str,
        suffix: str | None = None,
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
        versioned_grid_id_match = self.match_grid_id(versioned_grid_id)
        if versioned_grid_id_match is None:
            raise ValueError(
                f"Invalid grid_id: {versioned_grid_id}, expected format: {GRID_ID_REGEX.pattern}"
            )

        # Check if corresponding grid exists
        grid_path = self.grids_path.joinpath(versioned_grid_id)
        if not grid_path.exists():
            raise FileNotFoundError(
                f"Grid with id {versioned_grid_id} does not exist. Please add grid first."
            )

        if not date:
            # Get date where result folder was created
            result_path_stat = os.stat(results_path)
            date = datetime.fromtimestamp(result_path_stat.st_mtime)

        # Add result data
        res_id = self.create_res_id(versioned_grid_id, date, suffix)
        destination_dir = self.results_path.joinpath(res_id)
        if destination_dir.exists():
            raise FileExistsError(f"Results with id {res_id} already exists.")
        if move:
            os.rename(results_path, destination_dir)
        else:
            shutil.copytree(results_path, destination_dir)

    def create_grid_id(self, grid_id: str) -> str:
        match = self.match_grid_id(grid_id)
        if match:
            grid_id = match[0]
        grids = self.list_grids(grid_id)
        if grids:
            max_version = 1
            for grid in grids:
                match = self.match_grid_id(grid)
                if match:
                    _, version = match
                    if version > max_version:
                        max_version = version
            version = max_version + 1
        else:
            version = 1
        grid_id = f"{grid_id}-v{version}"
        match = GRID_ID_REGEX.match(grid_id)
        assert match, f"Invalid grid_id: {grid_id}"
        return grid_id

    @staticmethod
    def match_grid_id(grid_id) -> tuple[str, int] | None:
        """Matches grid_id and returns grid_id and grid_version or None."""
        match = GRID_ID_REGEX.match(grid_id)
        if match:
            grid_id, grid_version = match.groups()
            return grid_id, int(grid_version)
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

    # TODO: Check if method always creats unused ids
    @staticmethod
    def create_res_id(
        grid_id: str, date: datetime | None = None, suffix: str | None = None
    ) -> str:
        if not date:
            date = datetime.now()
        res_id = f"{date.strftime('%Y_%m_%d')}-{grid_id}"
        if suffix:
            res_id = res_id + f"-{suffix}"
        match = RESULT_ID_REGEX.match(res_id)
        assert match, f"Invalid res_id: {res_id}"
        return res_id

    def adjust_conf_path(self, conf: ConfigTree, new_grid_path: str):
        grid_paths_to_adjust = [
            "simona.input.grid.datasource.csvParams.directoryPath",
            "simona.input.primary.csvParams.directoryPath",
        ]

        updated = deepcopy(conf)
        for p in grid_paths_to_adjust:
            if p in conf:
                updated.put(p, new_grid_path)
            else:
                raise ValueError(f"Path {p} not found in config.")

        grid_id = Path(new_grid_path).name
        res_id = self.create_res_id(grid_id)
        output_conf = "simona.output.base.dir"

        if output_conf in updated:
            updated.put(output_conf, os.path.join(self.results_path, res_id))
            updated.put("simona.output.base.addTimestampToOutputDir", "false")

        updated.put("siona.simulationName", res_id)

        slack_volt_src = "simona.input.grid.slackVoltageSource.directoryPath"
        if slack_volt_src in conf:
            sl_volt_path = conf.get(slack_volt_src)
            if sl_volt_path:
                file_name = Path(sl_volt_path).name
                new_sl_volt_path = os.path.join(new_grid_path, file_name)
                updated.put(slack_volt_src, new_sl_volt_path)

        return updated
