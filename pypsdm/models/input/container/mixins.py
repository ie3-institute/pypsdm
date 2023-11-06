import logging
from abc import ABC, abstractmethod

from pypsdm.errors import ComparisonError


class ContainerMixin(ABC):
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        for a, b in zip(
            self.to_list(include_empty=True), other.to_list(include_empty=True)
        ):
            if a != b:
                return False
        return True

    def __bool__(self):
        return len(self.to_list(include_empty=False)) > 0

    @abstractmethod
    def to_list(self, include_empty: bool = False) -> list:
        pass

    @classmethod
    @abstractmethod
    def create_empty(cls):
        pass

    def to_csv(self, path: str, mkdirs=False, delimiter: str = ","):
        for entities in self.to_list():
            try:
                entities.to_csv(path, delimiter=delimiter, mkdirs=mkdirs)
            except Exception as e:
                logging.error(f"Could not write {type(entities)} to {path}. Error: {e}")

    def compare(self, other) -> None:
        """
        Compares the grid with another grid, and raises an error if they are not equal.
        """
        if not isinstance(other, type(self)):
            raise ComparisonError(
                f"Type of self {type(self)} != type of other {type(other)}"
            )
        errors = []

        list_a = self.to_list(include_empty=True)
        types_a = [type(e) for e in list_a]
        list_b = other.to_list(include_empty=True)
        types_b = [type(e) for e in list_b]

        if types_a != types_b:
            raise ComparisonError(
                f"Non empty container elements differ: {types_a} != {types_b}"
            )

        for a, b in zip(list_a, list_b):
            try:
                a.compare(b)
            except ComparisonError as e:
                errors += [e]

        if errors:
            raise ComparisonError(
                f"Comparison of {type(self)} failed.", differences=errors
            )
