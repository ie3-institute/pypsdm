from pypsdm.models.enums import EntitiesEnum, RawGridElementsEnum
from pypsdm.models.result.participant.dict import EntitiesResultDictMixin
from pypsdm.models.ts.base import EntityKey
from pypsdm.models.ts.types import ComplexVoltageDict


class NodesResult(ComplexVoltageDict[EntityKey], EntitiesResultDictMixin):
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other)

    @classmethod
    def entity_type(cls) -> EntitiesEnum:
        return RawGridElementsEnum.NODE
