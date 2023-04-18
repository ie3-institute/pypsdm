import json

from pandas import Series
import plotly.express as px
import plotly.graph_objs as go

from psdm_analysis.models.input.container.grid_container import GridContainer


def get_lons_lats(geojson: str):
    coordinates = json.loads(geojson)["coordinates"]
    return list(zip(*coordinates))  # returns lons, lats


def grid_plot(grid: GridContainer):
    def add_line_trace(line_data: Series):
        lons, lats = get_lons_lats(line_data.geo_position)
        fig.add_trace(
            go.Scattermapbox(
                mode="lines",
                lon=lons,
                lat=lats,
                hoverinfo="skip",
            )
        )

    def to_hover_text(data_dict: dict):
        return "<br>" + "<br>".join(
            [f"{key}={value}" for key, value in data_dict.items()]
        )

    node_hover_data = grid.get_nodal_sp_count_and_power()
    text = grid.raw_grid.nodes.data.index.map(
        lambda id: to_hover_text(node_hover_data[id])
    )
    fig = px.scatter_mapbox(
        grid.raw_grid.nodes.data,
        lat="latitude",
        lon="longitude",
        hover_name="id",
        text=text,
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    grid.raw_grid.lines.data.apply(lambda line: add_line_trace(line), axis=1)
    return fig
