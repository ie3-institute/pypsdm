import os
from json import loads
from typing import Optional
from uuid import uuid4

import pandas as pd
from pandas.errors import DataError

from pypsdm.io.utils import is_valid_uuid, normaldistribution
from pypsdm.models.input.participant.evcs import EvcsLocationType


def create_dummy_public_pois(node_for_public_pois):

    geo_position_public_pois = loads(node_for_public_pois.geo_position)
    longitude_public_pois, latitude_public_pois = geo_position_public_pois[
        "coordinates"
    ]

    data_poi = {
        "uuid": [
            "3ae3a120-a4ab-4057-8b48-022d8b952930",
            "52c73a61-a600-4e02-8ed0-24822cef0aa4",
            "523770be-10a6-4c39-929e-2ed4fc82ff19",
            "8555fdc8-6f8c-40c6-b467-86c3b745e163",
            "a2fdb223-c1ec-4ad9-b558-0f145e4ffd8d",
            "1abce734-a83b-476f-a543-795e60bfe0a2",
            "1a6123e8-3c36-4ffd-a753-234edaaf391e",
            "a1554878-6129-4434-bc54-7111dd20d7ee",
            "020d2e8a-c93a-4042-9972-949e8a6ac2ad",
            "145b3ab5-74a2-4171-b82f-0c7316d45d60",
        ],
        "id": [
            "Culture-poi",
            "Sports-poi",
            "RELIGIOUS-poi",
            "Work-poi",
            "Supermarket-poi",
            "Services-poi",
            "Other_Shop-poi",
            "Medicical-poi1",
            "BBPG-poi",
            "Restaurant-poi",
        ],
        "size": [500, 500, 500, 500, 500, 500, 500, 500, 500, 500],
        "lat": [
            latitude_public_pois,
            latitude_public_pois,
            latitude_public_pois,
            latitude_public_pois,
            latitude_public_pois,
            latitude_public_pois,
            latitude_public_pois,
            latitude_public_pois,
            latitude_public_pois,
            latitude_public_pois,
        ],
        "lon": [
            longitude_public_pois,
            longitude_public_pois,
            longitude_public_pois,
            longitude_public_pois,
            longitude_public_pois,
            longitude_public_pois,
            longitude_public_pois,
            longitude_public_pois,
            longitude_public_pois,
            longitude_public_pois,
        ],
        "categoricallocation": [
            "culture",
            "sports",
            "religious",
            "work",
            "supermarket",
            "services",
            "other_shop",
            "medicinal",
            "bbpg",
            "restaurant",
        ],
    }
    df_poi = pd.DataFrame(data_poi)
    df_poi.set_index("uuid", inplace=True)

    data_poi_map = {
        "poi": [],
        "evcs": [],
        "evs": [],
    }
    df_poi_map = pd.DataFrame(data_poi_map)
    df_poi_map.set_index("poi", inplace=True)

    # Add Home POI WITHOUT charging
    no_charge_home_uuid = "bbf19030-9cea-4c49-bec8-acbfe86ca717"
    new_row_poi = {
        "id": "HOME_WITHOUT_CHARGING-poi",
        "size": 500,
        "lat": latitude_public_pois,
        "lon": longitude_public_pois,
        "categoricallocation": "home",
    }
    df_poi.loc[no_charge_home_uuid] = new_row_poi
    return df_poi, df_poi_map


def enrich_grid_by_evs_and_evcs(
    nodes,
    ev_p_rated_params: list,
    evcs_v2g: bool = False,
    controlling_em: bool = False,
    df_public_poi: Optional[pd.DataFrame] = None,
    df_public_poi_map: Optional[pd.DataFrame] = None,
):
    if df_public_poi is not None and df_public_poi_map is not None:
        df_poi = df_public_poi
        df_poi_map = df_public_poi_map
    else:
        df_poi, df_poi_map = create_dummy_public_pois(nodes.iloc[0])

    def create_ev_data_dict(this_node):
        ev_uuid = uuid4()
        ev_type_uuid = uuid4()
        ev_p_rated = normaldistribution(ev_p_rated_params)

        return {
            "id": f"EV_{this_node.id}",
            "uuid": ev_uuid,
            "type_uuid": ev_type_uuid,
            "node": str(this_node.Index),
            "s_rated": ev_p_rated,  # AC
            "s_ratedDC": ev_p_rated,  # DC
            "e_storage": 120.0,
            "e_cons": 0.18,
        }

    def create_evcs_data_dict(this_node):
        evcs_uuid = uuid4()
        evcs_id = f"EVCS_{this_node.id}"

        return {
            "id": evcs_id,
            "uuid": evcs_uuid,
            "node": str(this_node.Index),
            "location_type": EvcsLocationType.HOME.value,
            "s_rated": 22.0,
            "v2g_support": str(evcs_v2g).lower(),
            "controlling_em": get_em_uuid(controlling_em),
        }

    def get_em_uuid(em: bool):
        em_uuid = "fixme"

        if em:
            if em_uuid and is_valid_uuid(em_uuid):
                return em_uuid
            else:
                raise DataError(
                    "EVCS should be connected to EM but no valid UUID of an EM could be found."
                )

        return ""

    # Initialize dictionaries for EV and EVCS data
    ev_dict = {
        "id": [],
        "uuid": [],
        "type_uuid": [],
        "node": [],
        "s_rated": [],
        "s_ratedDC": [],
        "e_storage": [],
        "e_cons": [],
    }

    evcs_dict = {
        "id": [],
        "uuid": [],
        "node": [],
        "location_type": [],
        "s_rated": [],
        "v2g_support": [],
        "controlling_em": [],
    }

    for node in nodes.itertuples(index=True):

        # Create EV and EVCS data dictionaries and append them to respective lists in dicts
        current_ev_data = create_ev_data_dict(node)
        current_evcs_data = create_evcs_data_dict(node)

        for key in ev_dict.keys():
            ev_dict[key].append(current_ev_data[key])

        for key in evcs_dict.keys():
            evcs_dict[key].append(current_evcs_data[key])

        geo_position = loads(node.geo_position)
        longitude, latitude = geo_position["coordinates"]

        # POI Mapping
        poi_uuid = uuid4()

        df_poi.loc[poi_uuid] = {
            "uuid": poi_uuid,
            "id": f"POI_EVCS_{node.id}",
            "size": 1,
            "lat": latitude,
            "lon": longitude,
            "categoricallocation": "home",
        }

        df_poi_map.loc[poi_uuid] = {
            "poi": poi_uuid,
            **{
                key: value
                for key, value in zip(
                    ["evcs", "evs"],
                    [current_evcs_data["uuid"], current_ev_data["uuid"]],
                )
            },
        }

    return (ev_dict, evcs_dict, df_poi, df_poi_map)


def add_pois_of_enriched_evcs(df_poi, df_poi_map, target_grid_path):
    pois_path = os.path.join(target_grid_path, "pois")

    if not os.path.exists(pois_path):
        os.mkdir(pois_path)
    df_poi.to_csv(pois_path + "/poi.csv", index_label="uuid")
    df_poi_map.to_csv(pois_path + "/poi_mapping.csv", index=True)
