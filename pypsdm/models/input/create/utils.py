import json
import re

import pandas as pd

from pypsdm.models.enums import EntitiesEnum
from pypsdm.models.input.container.grid import GridContainer
from pypsdm.models.input.entity import Entities


def create_data(data_dict, data_func, entity_preprocessing: EntitiesEnum | None = None):
    nr_items = {len(values) for values in data_dict.values()}
    if not len(nr_items) == 1:
        raise ValueError(f"Number of items in each list must be equal. Got {nr_items}.")
    data = pd.concat(
        [
            data_func(**dict(zip(data_dict.keys(), values)))
            for values in zip(*data_dict.values())
        ],
        axis=1,
    ).T
    if entity_preprocessing:
        data = Entities.preprocessing(entity_preprocessing, data)
    return data


def generate_function_from_attributes(cls, file_path):
    """Generate function strings for each subclass and write them to a file."""
    subclass_function_strings = _generate_function_from_attributes(cls)
    with open(file_path, "w") as file:
        file.write("import pandas as pd\n\n\n")
        for classname, function_string in subclass_function_strings.items():
            file.write(function_string + "\n\n")  # Two newlines for separation


def _generate_function_from_attributes(cls):
    """Generate create_data functions based on type attributes."""

    def get_all_subclasses(cls):
        """Recursively get all subclasses of a given class"""
        subclasses = cls.__subclasses__()
        for subclass in list(
            subclasses
        ):  # Use list to create a copy since we'll be modifying the subclasses list
            subclasses.extend(get_all_subclasses(subclass))
        return subclasses

    def camel_to_snake(s: str) -> str:
        s1 = re.sub(
            "(.)([A-Z][a-z]+)", r"\1_\2", s
        )  # Identify words in CamelCase and add underscore
        return re.sub(
            "([a-z0-9])([A-Z])", r"\1_\2", s1
        ).lower()  # Convert the string to lowercase

    subclasses = get_all_subclasses(cls)
    function_strings = {}

    for subclass in subclasses:
        attributes = subclass.attributes()
        # non_default = attributes - default_attributes.keys()
        # default = default_attributes - attributes.keys()
        args_str = ",\n\t".join(attributes)  # Formatting each argument on a new line
        series_items_str = ",\n\t\t".join(
            [f'"{attr}": {attr}' for attr in attributes]
        )  # Formatting items in pd.Series
        function_str = f"""def create_{camel_to_snake(subclass.__name__)}_data(
\t{args_str}
):
\treturn pd.Series({{
\t\t{series_items_str}
\t}})"""
        function_strings[subclass.__name__] = function_str

    return function_strings


def update_line_geo_pos_from_coords(grid: GridContainer):
    nodes = grid.raw_grid.nodes

    def get_coord(uuid):
        lat = nodes.latitude[uuid]
        lon = nodes.longitude[uuid]
        return [lon, lat]

    for uuid, line in grid.raw_grid.lines.data.iterrows():
        geo_pos = line.geo_position
        node_a_uuid = line.node_a
        node_b_uuid = line.node_b
        geo_json = json.loads(geo_pos)
        geo_json["coordinates"] = [get_coord(node_a_uuid), get_coord(node_b_uuid)]
        grid.raw_grid.lines.data.loc[uuid, "geo_position"] = str(json.dumps(geo_json))
