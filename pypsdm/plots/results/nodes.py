import matplotlib.pyplot as plt
from matplotlib import gridspec

from pypsdm.models.gwr import GridWithResults
from pypsdm.plots.common.utils import FIGSIZE
from pypsdm.plots.results.power_plot import ax_plot_nodal_ps_violin
from pypsdm.plots.results.voltage_plot import ax_plot_v_mags_violin


def voltage_power_along_branches_violin(gwr: GridWithResults):
    branches = gwr.grid.raw_grid.get_branches()
    nodes_res = gwr.build_enhanced_nodes_result()
    width, height = FIGSIZE
    height = height * len(branches) * 2
    fig = plt.figure(figsize=(width, height))
    outer_grid = gridspec.GridSpec(len(branches), 1, wspace=0.2, hspace=0.3)
    inner_grids = []
    for i, branch in enumerate(branches):
        inner_grid = gridspec.GridSpecFromSubplotSpec(
            2, 1, subplot_spec=outer_grid[i], wspace=0.1, hspace=0.6
        )
        inner_grids.append(inner_grid)
        ax_v = plt.Subplot(fig, inner_grid[0])
        ax_plot_v_mags_violin(ax_v, nodes_res, branch)
        ax_v.set_title(f"Voltage and Active Power for Branch {i}")
        fig.add_subplot(ax_v)

        ax_p = plt.Subplot(fig, inner_grid[1])
        ax_plot_nodal_ps_violin(ax_p, nodes_res, branch)
        fig.add_subplot(ax_p)

    plt.tight_layout()
    plt.show()

    return fig, outer_grid, inner_grids
