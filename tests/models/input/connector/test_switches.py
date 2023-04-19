from tests.utils import compare_dfs


def test_to_csv(grid, tmp_path, delimiter):
    switches = grid.raw_grid.switches
    switches.to_csv(str(tmp_path), delimiter)
    switches2 = switches.from_csv(str(tmp_path), delimiter)
    compare_dfs(switches.data, switches2.data)
