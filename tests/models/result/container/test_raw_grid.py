import pandas as pd

from pypsdm.models.enums import EntitiesEnum
from pypsdm.models.result.container.raw_grid import RawGridResultContainer
from pypsdm.models.ts.base import TIME_COLUMN_NAME, EntityKey


def get_entities_test_data(entity: EntitiesEnum):
    def get_data(attributes):
        data = pd.DataFrame(
            {
                TIME_COLUMN_NAME: [
                    "2021-01-01",
                    "2021-01-02",
                    "2021-01-03",
                    "2021-01-04",
                ],
            }
        )
        for attr in attributes:
            data[attr] = [0.0, 1.0, 2.0, 3.0]
        return data

    entities = {}
    for e in ["a", "b", "c"]:
        res_type = entity.get_result_type()
        entities[EntityKey(e)] = res_type(get_data(res_type.attributes()))

    return entity.get_result_dict_type()(entities)  # type: ignore


def get_container() -> RawGridResultContainer:
    return RawGridResultContainer(
        {e: get_entities_test_data(e) for e in RawGridResultContainer.entity_keys()}
    )


def test_from_csv(result_path_sb):
    grid = RawGridResultContainer.from_csv(result_path_sb)
    assert len(grid.nodes) == 147
    assert len(grid.lines) == 147
    assert len(grid.transformers_2w) == 1


def test_to_csv(tmp_path):
    grid = get_container()
    grid.to_csv(tmp_path)
    grid2 = RawGridResultContainer.from_csv(tmp_path)
    assert grid == grid2
