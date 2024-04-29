import pytest

from pypsdm.models.input.container.participants import SystemParticipantsContainer


@pytest.fixture(scope="module")
def participants(input_path_sg):
    return SystemParticipantsContainer.from_csv(input_path_sg)


def test_spa_container_from_csv(participants):
    assert len(participants.loads) == 3
    assert len(participants.pvs) == 3
    assert len(participants.biomass_plants) == 0
    assert len(participants.wecs) == 0


def test_filter_by_node(participants):
    filtered = participants.filter_by_nodes("b7a5be0d-2662-41b2-99c6-3b8121a75e9e")
    assert len(filtered.loads) == 1
    assert len(filtered.pvs) == 1


def test_create_empty():
    empty_participants = SystemParticipantsContainer.empty()
    if empty_participants:
        raise AssertionError("Empty participants should be falsy")
