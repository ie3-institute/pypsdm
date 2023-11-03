from uuid import uuid4

import pandas as pd

from pypsdm.models.input.container.grid import GridContainer


def create_poi(
    id: str,
    lat: float,
    lon: float,
    categorical_location: str,
    size: float = 1,
    uuid: str | None = None,
):
    if uuid is None:
        uuid = str(uuid4())
    return pd.Series(
        {
            "id": id,
            "lat": lat,
            "lon": lon,
            "categoricallocation": categorical_location,
            "size": size,
        }
    ).rename(uuid)


def create_poi_mapping(
    grid: GridContainer, pre_existing_pois: pd.DataFrame | None = None
):
    """
    Utility method that creates home pois for all EVs of the grid and creates a mapping
    from the EVCS at a node to all EVs at that node.
    """
    poi_mappings = None
    if pre_existing_pois is not None:
        pois = pre_existing_pois
    else:
        pois = pd.DataFrame()
    evs = grid.participants.evs
    evcs = grid.participants.evcs
    nodes = grid.raw_grid.nodes
    for node in list(nodes.uuid):
        ev_uuids = list(evs.filter_by_nodes(node).uuid)
        evcs_uuids = list(evcs.filter_by_nodes(node).uuid)
        assert len(evcs_uuids) <= 1
        if evcs_uuids:
            evcs_uuid = evcs_uuids[0]
            if not ev_uuids:
                raise ValueError("EVCS without EV")
            poi = create_poi(
                id="HOME-poi",
                lat=nodes.latitude[node],  # type: ignore
                lon=nodes.longitude[node],  # type: ignore
                categorical_location="home",
            )
            pois = pd.concat([pois, poi.to_frame().T], axis=1)

            # Create POI mapping
            ev_str = "".join([f"{ev} " for ev in ev_uuids])
            poi_mapping = pd.Series({"poi": poi.name, "evcs": evcs_uuid, "evs": ev_str})
            if poi_mappings is None:
                poi_mappings = poi_mapping.to_frame()
            else:
                poi_mappings = pd.concat([poi_mappings, poi_mapping], axis=1)

    if poi_mappings is None:
        raise ValueError("No POI mappings created")

    return pois, poi_mappings.T
