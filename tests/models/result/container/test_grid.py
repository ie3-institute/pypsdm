from datetime import datetime

import pandas as pd

from pypsdm.models.enums import EntitiesEnum, RawGridElementsEnum
from pypsdm.models.result.container.grid import GridResultContainer
from pypsdm.models.result.container.participants import (
    SystemParticipantsResultContainer,
)
from pypsdm.models.result.container.raw_grid import RawGridResultContainer
from pypsdm.models.result.grid import CongestionResult
from pypsdm.models.ts.base import TIME_COLUMN_NAME, EntityKey, SubGridKey


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

    def get_congestion_data(subgrid: int):
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
        data["vMin"] = [0.9, 0.9, 0.9, 0.9]
        data["vMax"] = [1.1, 1.1, 1.1, 1.1]
        data["subgrid"] = [subgrid, subgrid, subgrid, subgrid]

        for attr in ["voltage", "line", "transformer"]:
            data[attr] = [False, False, False, False]
        return data

    entities = {}

    if entity is RawGridElementsEnum.SUBGRID:
        for s in [1, 2, 3]:
            entities[SubGridKey(s)] = CongestionResult(get_congestion_data(s))

    else:
        for e in ["a", "b", "c"]:
            res_type = entity.get_result_type()
            entities[EntityKey(e)] = res_type(get_data(res_type.attributes()))

    return entity.get_result_dict_type()(entities)  # type: ignore


def get_container() -> GridResultContainer:
    raw_grid = RawGridResultContainer(
        {e: get_entities_test_data(e) for e in RawGridResultContainer.entity_keys()}
    )
    participants = SystemParticipantsResultContainer(
        {
            e: get_entities_test_data(e)
            for e in SystemParticipantsResultContainer.entity_keys()
        }
    )
    return GridResultContainer(
        raw_grid=raw_grid,
        participants=participants,
    )


def test_from_csv(result_path_sb):
    grid = GridResultContainer.from_csv(result_path_sb)
    assert len(grid.nodes) == 147
    assert len(grid.lines) == 147
    assert len(grid.transformers_2w) == 1
    assert len(grid.loads) == 139


def test_to_csv(tmp_path):
    grid = get_container()
    grid.to_csv(tmp_path)
    grid2 = GridResultContainer.from_csv(tmp_path)
    assert grid == grid2


def test_interval():
    grid = get_container()
    start = datetime(2021, 1, 2)
    end = datetime(2021, 1, 3)
    filt = grid.interval(start, end)
    for participants in filt.participants.to_dict().values():
        for p in participants.values():
            assert p.data.index[0] >= start
            assert p.data.index[-1] <= end
            assert len(p) == 2

    for res in filt.raw_grid.to_dict().values():
        for r in res.values():
            assert r.data.index[0] >= start
            assert r.data.index[-1] <= end
            assert len(r) == 2
    assert grid[start:end] == filt
